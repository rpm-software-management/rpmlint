import contextlib
from fnmatch import fnmatch
import hashlib
from pathlib import Path
import re
import stat
import xml.etree.ElementTree as ET

from rpmlint.checks.AbstractCheck import AbstractCheck


DEFAULT_DIGEST_ALG = 'sha256'


# We support different "filters" for calculating file digests for whitelisting
# purposes. The reasoning behind this is that we want to detect *functional*
# changes to certain files but we don't want to be bothered by any other
# changes like changes in comments, copyright headers, whitespace and so on.
#
# To avoid such bogus changes showing up in the checker we can filter the
# target files depending on their file type. Currently we have two common
# special cases:
#
# - shell-like files (configuration files, shell scripts, Python
# scripts, Perl scripts etc) that can contain empty lines or comments
# introduced by '#'.
# - XML files for things like D-Bus configuration files or polkit policies.
# Here also XML style comments and whitespace can occur.
#
# The filter classes help in calculating a file digest for a filtered version
# of the target file that is normalized and therefore stable against the
# outlined kinds of changes. Since this makes getting the right whitelisting
# digests hard, a small companion tool in tools/get_whitelisting_digest.py
# exists.


class DefaultDigester:
    """This class performs the default digest calculation of arbitrary file
    contents as is."""

    def __init__(self, path, halg):
        self.path = path
        self.halg = halg

    def parse_content(self):
        # simply generate chunks on binary level
        with open(self.path, 'rb') as fd:
            while True:
                chunk = fd.read(4096)
                if not chunk:
                    break
                yield chunk

    def get_digest(self):
        """This returns the hash digest of the *un*filtered input file."""
        hasher = hashlib.new(self.halg)

        for chunk in self.parse_content():
            hasher.update(chunk)

        return hasher.hexdigest()


class ShellDigester(DefaultDigester):
    """This class performs digest calculation of shell style configuration
    files or scripts. Certain aspects like comments and whitespace will be
    filtered out of the digest calculation."""

    def parse_content(self):
        # generate filtered lines
        with open(self.path) as fd:
            for line_nr, line in enumerate(fd):
                stripped = line.strip()
                if not stripped:
                    # skip empty lines
                    continue
                elif line_nr == 0 and stripped.startswith('#!'):
                    # keep shebang lines mostly intact,
                    # but ignore minor interpreter versions
                    line = re.sub(r'\bpython3\.\d+\b', 'python3', line)
                elif stripped.startswith('#'):
                    # skip comments
                    # NOTE: we don't strip trailing comments like in
                    # 'if [ 5 -eq $NUM ]; then # compare to 5'
                    # because the danger would be too high to remove actual
                    # content instead of just comments
                    continue

                # don't use the completely stripped version, in Python for
                # example the indentation is part of the syntax and changes
                # here could change the meaning
                yield (line.rstrip() + '\n').encode()


class XmlDigester(DefaultDigester):
    """This class performs digest calculation of XML configuration files.
    Certain aspects like comments and whitespace will be filtered out of the
    digest calculation."""

    def parse_content(self):
        # NOTE: the ElementTree is not robust against malicious input. Rpmlint
        # processes a lot of untrusted input. In the OBS context this only
        # happens within the virtual machines where packagers can manipulate a
        # lot of things anyway so it should be okay.

        # this returns a canonicalized form of the XML without comments or
        # anything. It is missing the XML preamble and DOCTYPE declaration,
        # though. It's as good as I could get it to be without parsing XML on
        # foot or relying on third party XML modules.

        # chunked / line wise processing is likely impossible for XML so
        # return the whole bunch
        yield ET.canonicalize(from_file=self.path, strip_text=True).encode()


# These values can be used in the individual "digests" entries of a
# whitelisting entry for a given digest group. For example:
# { path = "/some/path.xml", algorithm = "sha256", digester = "xml", hash = "..." }
DIGESTERS = {
    'default': DefaultDigester,
    'shell': ShellDigester,
    'xml': XmlDigester,
}


class FileDigestCheck(AbstractCheck):

    def __init__(self, config, output):
        super().__init__(config, output)
        # gather different FileDigestCheck configurations in an list. Each entry
        # will be a dictionary like:
        #
        # {
        #     "FollowSymlinks": True,
        #     "Locations: ["/path/one", "/path/two"],
        #     "NamePatterns: ["*.so"],
        #     "type": "pam"
        # }
        self.checks = []
        # maps from a check type name like "pam" to its configuration dict as
        # found in self.checks
        self.known_check_types: dict[str, dict] = {}

        for name, config in self.config.configuration['FileDigestLocation'].items():
            # convert the Location paths into Path objects
            config['Locations'] = [Path(p) for p in config['Locations']]
            # make sure these keys always exists
            config.setdefault('NamePatterns', [])
            config.setdefault('FollowSymlinks', False)
            config['type'] = name
            self.checks.append(config)
            self.known_check_types[name] = config

        self._setup_digest_location_trie()
        self.ghost_file_exceptions = self.config.configuration.get('GhostFilesExceptions', [])
        self.symlink_exceptions = self.config.configuration.get('SymlinkExceptions', [])

        self.digest_cache = {}

        self.digest_groups = self.config.configuration.get('FileDigestGroup', [])
        for digest_group in self.digest_groups:
            self._normalize_digest_group(digest_group)
            self._sanity_check_digest_group(digest_group)

        for exc in self.ghost_file_exceptions:
            self._sanity_check_package_keys('GhostFilesExceptions', exc)
        for exc in self.symlink_exceptions:
            self._sanity_check_package_keys('SymlinkExceptions', exc)

    def _get_digester(self, digest_info):
        """Returns the proper digester instance for the given digest_info
        dictionary as found in a file digest group."""
        name = digest_info.get('digester', 'default')
        try:
            return DIGESTERS[name]
        except KeyError:
            path = digest_info['path']
            raise Exception(f'Invalid digester {name} encountered for path {path}')

    def _setup_digest_location_trie(self):
        """Builds a trie data structure for quickly determining if a path is
        in a restricted location."""
        self.restricted_paths_trie = {}
        # Build a trie of restricted paths across all checks
        for config in self.checks:
            for path in config['Locations']:
                if not path.is_absolute():
                    raise Exception(f'Absolute path expected: {path}')
                node = self.restricted_paths_trie
                # Skip initial '/'.
                parts = path.parts[1:]
                for part in parts[:-1]:
                    node = node.setdefault(part, {})
                    if node is None:
                        # a terminator was already set here, so we cannot
                        # enter this additional path into the trie.
                        raise Exception(f'Conflicting paths in trie {path}')
                node[parts[-1]] = None

    def _is_path_restricted(self, path):
        """
        Return true if there is a check configuration that restricts the given
        path.
        """
        if isinstance(path, str):
            path = Path(path)

        node = self.restricted_paths_trie
        # Skip initial '/'
        for part in path.parts[1:]:
            if node is None:
                # terminator found, this path prefix is indeed restricted by a check
                return True
            elif part not in node:
                # path element not in trie, not restricted
                return False
            node = node[part]
        # `path` is a prefix of a restricted path, but not within a restricted location
        return False

    def _normalize_digest_group(self, digest_group):
        """Perform any operations on the digest_group to make it match the
        structure excepted by the rest of the checker.

        Some convenience functionality like the nodigests list needs to be
        translated into something that is easier to process by the check.
        """
        # expand short form 'nodigests' into full configuration entries which
        # are more easily processable by us.
        for no_digest_path in digest_group.get('nodigests', []):
            digests = digest_group.setdefault('digests', [])
            digests.append(
                {
                    'path': no_digest_path,
                    'algorithm': 'skip',
                    'hash': '',
                }
            )

        for digest in digest_group.get('digests', []):
            # imply default algorithm
            digest.setdefault('algorithm', DEFAULT_DIGEST_ALG)

    def _sanity_check_digest_group(self, digest_group):
        check_type = digest_group['type']
        if check_type not in self.known_check_types:
            raise KeyError(f'FileDigestGroup type "{check_type}" is not '
                           f'supported, known values: {self.known_check_types.keys()}')

        for digest in digest_group['digests']:
            # verify digest algorithm
            algorithm = digest['algorithm']
            if algorithm == 'skip':
                pass
            else:
                # this will raise on bad algorithm names
                hashlib.new(algorithm)

            if 'path' not in digest:
                raise KeyError('FileDigestCheck: missing "path" key in FileDigestGroup entry')

            # verify a valid digester is selected, if any
            self._get_digester(digest)

        self._sanity_check_package_keys('FileDigestGroup', digest_group)

    def _sanity_check_package_keys(self, context, d):
        """Verifies package/packages keys in the given dictionary `d`.

        This supports a single `package = "name"` key as well as a `packages =
        ["one", "two"]` list. Sanity checks are performed verifying that at
        least one package is specified, the value types match but not both
        keys are present.

        context should be a string label for adding context to error messages.
        """

        package = d.get('package', None)
        packages = d.get('packages', [])

        if not package and not packages:
            raise KeyError(f'FileDigestCheck: missing "package" or "packages" key in {context}')
        elif package and packages:
            raise KeyError(f'FileDigestCheck: encountered both "package" and "packages" keys in {context}')

        if package and not isinstance(package, str):
            raise KeyError(f'FileDigestCheck: "package" key contains non-string value in {context}')
        elif packages and not isinstance(packages, list):
            raise KeyError(f'FileDigestCheck: "packages" key contains non-list value in {context}')

    def _gather_packages_from_dict(self, d):
        """returns a list of packages specified in a dictionary.

        This supports both a single `package="name"` key as well as a list of
        `packages=["one", "two"]`. Use _verify_package_keys_in_dict() to verify
        consistency before using this function."""
        pkg = d.get('package', None)
        if pkg:
            return [pkg]
        else:
            return d['packages']

    def _matches_pkg(self, config_dict, pkg):
        """Checks whether the given `config_dict` applies to the given package
        name.

        `config_dict` can be different types of configuration dicts for
        file digest groups, symlink and ghost exceptions as long as it
        supports `package` / `packages` keys.

        This function also resolves glob patterns.
        """
        for candidate in self._gather_packages_from_dict(config_dict):
            if pkg.name == candidate:
                return True
            elif candidate.startswith('glob:'):
                pattern = candidate.split(':', 1)[1]
                if fnmatch(pkg.name, pattern):
                    return True

        return False

    def _lookup_check_for_file(self, pkgfile):
        """Returns the dictionary of the FileDigestCheck config which applies
        to `pkgfile` or None if none applies."""
        if stat.S_ISDIR(pkgfile.mode):
            # directories are generally not restricted by this check
            return None

        # Make a fast lookup in the prepared trie of configuration locations
        path = Path(pkgfile.name)
        if not self._is_path_restricted(path):
            return None

        for config in self.checks:
            for location in config['Locations']:
                with contextlib.suppress(ValueError):
                    if path.relative_to(location):
                        if not config['NamePatterns']:
                            # files in this location are unconditionally subject to the check.
                            return config
                        else:
                            # we need to check if the filename matches the configured pattern.
                            for glob in config['NamePatterns']:
                                if fnmatch(path.name, glob):
                                    return config

        # must be a file which isn't matched by a name pattern.
        return None

    def _check_digest(self, digest_info, pkg):
        """Returns a tuple of (bool, str), where the boolean indicates whether
        the digest of the package's file matches the one recorded in the
        digest_info; the str contains the actual hash digest calculated
        from the package's file or None if no hash digest is configured or an
        error occurred."""
        algorithm = digest_info['algorithm']
        path = digest_info['path']
        if algorithm == 'skip':
            return (True, None)

        pkgfile = self._resolve_links(pkg, path)
        if pkgfile is None:
            return (False, None)

        digester = self._get_digester(digest_info)
        file_digest = self._calc_digest(digester, pkgfile, algorithm)
        return (file_digest == digest_info['hash'], file_digest)

    def _resolve_links(self, pkg, path):
        """Follows symbolic links within the package until a non-symlink entry
        is found. This cannot follow symlinks outside of the current
        package. If no valid target is found then None is returned, the
        resolved file entry otherwise."""
        pkgfile = pkg.files[path]
        while pkgfile and stat.S_ISLNK(pkgfile.mode):
            pkgfile = pkg.readlink(pkgfile)

        return pkgfile

    def _calc_digest(self, digester, pkgfile, algorithm):
        """Calculates the hash digest of `pkgfile` based on `algorithm` and
        `digester."""
        # include the digester in the cache key, because different entries
        # might be using different digester types for the same paths.
        cache_key = (id(digester), pkgfile.name, algorithm)

        digest = self.digest_cache.get(cache_key, None)
        if digest is not None:
            return digest

        digest = digester(pkgfile.path, algorithm).get_digest()

        self.digest_cache[cache_key] = digest
        return digest

    def _get_digest_hint(self, pkg, path):
        """Returns a string listing the observed digests of a path in case of
        whitelisting violations."""
        pkgfile = self._resolve_links(pkg, path)
        digest_hint = f'{DEFAULT_DIGEST_ALG} file digest'
        if not pkgfile:
            return f'{digest_hint}: <failed to resolve pkgfile>'

        if pkgfile.name != path:
            # make it clear that we resolved a symlink here
            digest_hint += f' of resolved path {pkgfile.name}'

        for dtype, digester in DIGESTERS.items():
            try:
                digest = self._calc_digest(digester, pkgfile, DEFAULT_DIGEST_ALG)
            except Exception:
                digest = '<failed-to-calculate>'

            digest_hint += f' {dtype} filter:{digest}'

        return digest_hint

    def _check_paths_match(self, rpm_path, whitelist_path):
        """This checks a whitelisted path against a file path found in the RPM
        if they match. This handles special cases like globbing characters in
        the whitelisting."""
        if rpm_path == whitelist_path:
            # exact match
            return True
        elif whitelist_path.startswith('glob:'):
            pattern = whitelist_path.split(':', 1)[1]
            return fnmatch(rpm_path, pattern)
        else:
            return False

    def _find_digest_groups(self, pkg, check):
        ret = []
        for group in self.digest_groups:
            if group['type'] == check['type'] and self._matches_pkg(group, pkg):
                ret.append(group)
        return ret

    def _check_for_unauthorized(self, pkg, check, restricted_paths):
        """Detect and complain about files with missing whitelistings.

        Returns the list of paths which are basically whitelisted (but digests
        still need to be checked).

        Params:
        - check: check configuration dictionary.
        - restricted_paths: list of restricted paths found in this package e.g. [
            '/usr/share/dbus-1/system-services/org.freedesktop.PolicyKit1.service',
            '/usr/share/dbus-1/system.d/org.freedesktop.PolicyKit1.conf'
          ]
        """
        # Collect all paths for the given check and package that are whitelisted
        known_paths = []
        for group in self._find_digest_groups(pkg, check):
            paths = [info['path'] for info in group['digests']]
            known_paths.extend(paths)

        known_paths = sorted(set(known_paths))

        # here the remaining paths that have whitelisting entries will be collected
        whitelisted = []

        for restricted in restricted_paths:
            for known in known_paths:
                # path is basically whitelisted somewhere, digest might still be wrong
                if self._check_paths_match(restricted, known):
                    whitelisted.append(restricted)
                    break
            else:
                digest_hint = self._get_digest_hint(pkg, restricted)
                check_name = check['type']
                self.output.add_info('E', pkg, f'{check_name}-file-unauthorized', restricted, f'({digest_hint})')

        return whitelisted

    def _check_digest_group(self, pkg, check: dict, group: dict,
                            verified_paths: set, mismatches: dict[str, list]):
        """Verify digests from the given digest group.

        The caller must ensure that `group` is valid for `pkg`.

        This verifies a digest group as a set of related paths: The
        whitelisting will only be considered complete if all files in the
        group have valid digests.

        If the group matches then the validated files will be added to
        `verified_paths`. Otherwise if digest mismatches have been found
        then these mismatches will be recorded in the dictionary `mismatches`.
        """

        missing_files = []
        valid_files = []
        found_mismatch = False
        check_name = check['type']
        # we need to handle mismatches for paths in unrelated locations specially
        unrelated_mismatches = {}

        # check all digests of the group if they have matching files in the package
        for digest_info in group['digests']:
            path = digest_info['path']
            # Check if digest whitelist path has a matching file in our package
            if not pkg.files.get(path):
                # This digest entry might not be needed anymore.
                #
                # We are tolerating that some of the listed files are no
                # longer present as long as any existing files have valid
                # digests.
                #
                # NOTE: glob patterns not supported here yet, but coupling
                # glob patterns with digests would be weird anyway.
                if not path.startswith('glob:'):
                    missing_files.append(path)
                continue

            try:
                valid, hashsum = self._check_digest(digest_info, pkg)
            except Exception as e:
                self.output.add_info('E', pkg, f'{check_name}-file-parse-error', path, f'failed to calculate digest: {e}')
                continue

            if valid:
                # Valid digest found, continue with the rest of the paths in this group
                valid_files.append(path)
            else:
                found_mismatch = True

            if hashsum:
                # also store the digest we encountered for later reference
                digest_info['encountered'] = hashsum
                # Record this digest mismatches for later error messages
                if self._is_path_restricted(path):
                    mismatch_list = mismatches.setdefault(path, [])
                else:
                    mismatch_list = unrelated_mismatches.setdefault(path, [])

                mismatch_list.append(digest_info)

        if valid_files and unrelated_mismatches:
            # only store unrelated file mismatches if any actually
            # restricted path was valid, otherwise this could create confusion
            # and too much noise.
            for unrelated, infos in unrelated_mismatches.items():
                mismatch_list = mismatches.setdefault(unrelated, [])
                mismatch_list.extend(infos)

        if found_mismatch:
            # this digest group is not fully valid for this package
            return

        for missing in missing_files:
            self.output.add_info('W', pkg, f'{check_name}-whitelisted-file-missing', missing, 'path present in whitelist but not in package')

        # the digest group was fully verified, we can add all files to the set
        # of verified paths.
        for file in valid_files:
            verified_paths.add(file)

    def _check_for_valid_digests(self, pkg, check, restricted_paths):
        """Check for valid digest entries for the given restricted paths.

        Ensures that all files in restricted locations are whitelisted in an
        appropriate file digest group. `restricted_paths` need to contain
        paths that are known to be whitelisted, but digest verification and
        group verification is still pending.

        Params:
        - check: check configuration dictionary.
        - restricted_paths: list of restricted and whitelisted paths found in this package e.g. [
            '/usr/share/dbus-1/system-services/org.freedesktop.PolicyKit1.service',
            '/usr/share/dbus-1/system.d/org.freedesktop.PolicyKit1.conf'
          ]
        """

        # digest mismatches will be recorded here with paths as keys and a
        # list of digest info dictionaries as values.
        mismatches: dict[str, list] = {}
        verified_paths = set()

        for group in self._find_digest_groups(pkg, check):
            self._check_digest_group(pkg, check, group, verified_paths, mismatches)

        violations = set()

        # now gather all whitelisting violations
        for restricted in restricted_paths:
            if restricted not in verified_paths:
                violations.add(restricted)

        # this here will collect "unrelated files", i.e. files that are not
        # directly in a restricted path but are listed as additional files
        # to verify in a digest group.
        for mismatch in mismatches:
            if mismatch not in verified_paths:
                violations.add(mismatch)

        for violation in sorted(violations):
            mismatch_list = mismatches.get(violation, [])
            if not mismatch_list:
                # This can happen if a group has mixed digest-coupled and
                # nodigest files. if the digest-coupled files fail to verify
                # then the nodigest files also fail to verify, since they are
                # treated as a group. No point in printing a
                # file-digest-mismatch in this case, though.
                continue

            hashes_seen = set()

            # in case multiple groups exist for the same file then we are
            # potentially printing multiple errors with multiple expected
            # hashes here, because we cannot really know which of the groups
            # is supposed to be the correct / desired one.
            for digest_info in mismatch_list:
                # print an error for each mismatch in case we have multiple
                # digest groups in which the path is listed.
                path = digest_info['path']
                alg = digest_info['algorithm']
                expected = digest_info['hash']
                hashsum = digest_info['encountered']
                if hashsum in hashes_seen:
                    # avoid printing duplicate errors
                    continue
                hashes_seen.add(hashsum)
                check_name = check['type']
                self.output.add_info('E', pkg, f'{check_name}-file-digest-mismatch', path,
                                     f'expected {alg}:{expected}, has:{hashsum}')

    def _is_ghost_allowed(self, pkg, path):
        """Check if a ghost file is in the exception list.

        In general we don't allow files we want to restrict to be included as
        %ghost. Some corner cases e.g. in polkit-default-privs make it
        necessary to ignore %ghost files. For these cases an exception list is
        maintained.

        Params:
        - pkg: name of the package
        - path: path of the %ghost file in the package
        """
        for ghost_exception in self.ghost_file_exceptions:
            if not self._matches_pkg(ghost_exception, pkg):
                continue
            if path in ghost_exception['paths']:
                return True
        return False

    def _is_symlink_allowed(self, pkg, path):
        """Check if a symlink file is in the exception list.

        For some checks we generally don't want to support symlinks at all,
        but certain corner cases make it necessary to ignore certain
        package/path combinations. For these cases an exception list is
        maintained.
        """
        for symlink_exception in self.symlink_exceptions:
            if not self._matches_pkg(symlink_exception, pkg):
                continue
            if path in symlink_exception['paths']:
                return True
        return False

    def check_binary(self, pkg):
        """
        Entry point for digest checks. Check that all files in restricted
        locations are covered by a file digest group in which all files have
        valid digests.
        """

        # Find all files in this package that are placed in restricted locations.

        # this maps the check name to the list of paths affected by it.
        restricted_paths: dict[str, list] = {}
        for pkgfile in pkg.files.values():
            check = self._lookup_check_for_file(pkgfile)
            path = pkgfile.name

            if not check:
                continue

            check_name = check['type']

            if path in pkg.ghost_files:
                if not self._is_ghost_allowed(pkg, path):
                    self.output.add_info('E', pkg, f'{check_name}-file-ghost', path)
            elif stat.S_ISLNK(pkgfile.mode) and not check['FollowSymlinks']:
                if not self._is_symlink_allowed(pkg, path):
                    self.output.add_info('E', pkg, f'{check_name}-file-symlink', path)
            else:
                file_list = restricted_paths.setdefault(check_name, [])
                file_list.append(path)

        # Check all found restricted files for every check type
        for check_name, files in restricted_paths.items():
            check = self.known_check_types[check_name]
            # filter out duplicates and sort the list of files to achieve
            # predictable behaviour of this check
            files = sorted(set(files))

            files = self._check_for_unauthorized(pkg, check, files)
            self._check_for_valid_digests(pkg, check, files)
