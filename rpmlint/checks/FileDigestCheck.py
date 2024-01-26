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
# - shell like files (configuration files, shell scripts, Python
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
        self.digest_configurations = {}
        # Build trie for fast lookup
        self.digest_configuration_trie = {}
        self.follow_symlinks_in_group = {}
        self.name_patterns_in_group = {}
        for group, values in self.config.configuration['FileDigestLocation'].items():
            self.digest_configurations[group] = [Path(p) for p in values['Locations']]
            self.follow_symlinks_in_group[group] = values['FollowSymlinks']
            self.name_patterns_in_group[group] = values.get('NamePatterns')

        self._setup_digest_location_trie()
        self.ghost_file_exceptions = self.config.configuration.get('GhostFilesExceptions', [])
        self.symlink_exceptions = self.config.configuration.get('SymlinkExceptions', [])

        self.digest_groups = self.config.configuration.get('FileDigestGroup', [])
        self.digest_cache = {}
        for digest_group in self.digest_groups:
            self._normalize_digest_group(digest_group)
            self._verify_digest_group(digest_group)

        for exc in self.ghost_file_exceptions:
            self._verify_package_keys_in_dict('GhostFilesExceptions', exc)
        for exc in self.symlink_exceptions:
            self._verify_package_keys_in_dict('SymlinkExceptions', exc)

    def _get_digester(self, entry):
        name = entry.get('digester', 'default')
        try:
            return DIGESTERS[name]
        except KeyError:
            path = entry['path']
            raise Exception(f'Invalid digester {name} encountered for path {path}')

    def _setup_digest_location_trie(self):
        # Build trie of Locations that are present in FileDigestLocation
        for config_locations in self.digest_configurations.values():
            for location in config_locations:
                path = Path(location)
                if not path.is_absolute():
                    raise Exception(f'Absolute path expected: {path}')
                node = self.digest_configuration_trie
                # Skip initial '/'.
                parts = path.parts[1:]
                for part in parts[:-1]:
                    node = node.setdefault(part, {})
                    if node is None:
                        raise Exception(f'Conflicting paths in trie {location}')
                node[parts[-1]] = None

    def _is_path_restricted(self, path):
        """
        Return true if there is a digest configuration that covers
        provided file at given path.
        """

        # Skip initial '/'
        parts = path.parts[1:]
        node = self.digest_configuration_trie
        for part in parts:
            if node is None:
                return True
            if part not in node:
                return False
            node = node[part]
        return False

    def _normalize_digest_group(self, digest_group):
        """Perform any operations on the digest_group to make it match the
        format excepted by the rest of the checker.

        Some convenience functionality like the nodigests list needs to be
        translated into something that is easier to process by the check.
        """
        # expand skip digests
        for skip_digest in digest_group.get('nodigests', []):
            digests = digest_group.setdefault('digests', [])
            digests.append(
                {
                    'path': skip_digest,
                    'algorithm': 'skip',
                    'hash': '',
                }
            )

        for digest in digest_group.get('digests', []):
            # imply sha256 digests by default
            digest.setdefault('algorithm', 'sha256')

    def _verify_digest_group(self, digest_group):
        dg_type = digest_group['type']
        if dg_type not in self.digest_configurations:
            raise KeyError(f'FileDigestGroup type "{dg_type}" is not '
                           f'supported, known values: {list(self.digest_configurations)}')

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

        self._verify_package_keys_in_dict('FileDigestGroup', digest_group)

    def _verify_package_keys_in_dict(self, context, d):
        """verifies package/packages keys in the given dictionary.

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
        for candidate in self._gather_packages_from_dict(config_dict):
            if pkg.name == candidate:
                return True
            elif candidate.startswith('glob:'):
                pattern = candidate.split(':', 1)[1]
                if fnmatch(pkg.name, pattern):
                    return True

        return False

    def _get_digest_configuration_group(self, pkgfile):
        if stat.S_ISDIR(pkgfile.mode):
            return None

        # Make quick lookup in the built trie of configuration locations
        path = Path(pkgfile.name)
        if not self._is_path_restricted(path):
            return None

        for group, locations in self.digest_configurations.items():
            for location in locations:
                with contextlib.suppress(ValueError):
                    if path.relative_to(location):
                        if not self.name_patterns_in_group[group]:
                            return group
                        else:
                            for glob in self.name_patterns_in_group[group]:
                                if fnmatch(path.name, glob):
                                    return group
        return None

    def _is_valid_digest(self, path, digest, pkg):
        algorithm = digest['algorithm']
        if algorithm == 'skip':
            return (True, None)

        pkgfile = self._resolve_links(pkg, path)
        if pkgfile is None:
            return (False, None)

        digester = self._get_digester(digest)
        file_digest = self._calc_digest(digester, pkgfile, algorithm)
        return (file_digest == digest['hash'], file_digest)

    def _resolve_links(self, pkg, path):
        pkgfile = pkg.files[path]
        while stat.S_ISLNK(pkgfile.mode):
            pkgfile = pkg.readlink(pkgfile)
            if not pkgfile:
                return None

        return pkgfile

    def _calc_digest(self, digester, pkgfile, algorithm):
        # include the digester in the cache key, because different entries
        # might be using different digester types
        cache_key = (id(digester), pkgfile.name, algorithm)

        digest = self.digest_cache.get(cache_key, None)
        if digest is not None:
            return digest

        digest = digester(pkgfile.path, algorithm).get_digest()

        self.digest_cache[cache_key] = digest
        return digest

    def _get_digest_hint(self, pkg, path):
        pkgfile = self._resolve_links(pkg, path)
        digest_hint = f'{DEFAULT_DIGEST_ALG} file digest'
        if not pkgfile:
            return digest_hint + ': <failed to resolve pkgfile>'

        if pkgfile.name != path:
            digest_hint += ' of resolved path ' + pkgfile.name

        for dtype, digester in DIGESTERS.items():
            try:
                digest = self._calc_digest(digester, pkgfile, DEFAULT_DIGEST_ALG)
            except Exception:
                digest = '<failed-to-calculate>'

            digest_hint += f' {dtype} filter:{digest}'

        return digest_hint

    def _check_paths_match(self, rpm_path, whitelist_path):
        """This checks a whitelisted path against a file path found in the RPM
        if they match. This also handles special cases like globbing
        characters in the whitelisting."""
        if rpm_path == whitelist_path:
            # exact match
            return True
        elif whitelist_path.startswith('glob:'):
            pattern = whitelist_path.split(':', 1)[1]
            return fnmatch(rpm_path, pattern)
        else:
            return False

    def _check_group_type(self, pkg, group_type, secured_paths):
        """ Check all secured files of a group type

        Ensures that all files in secured paths have to be whitelisted in an
        digest whitelisting belonging to group_type.

        Params:
        - group_type: type of digest group type e.g. "cron", "dbus", ...
        - secured_paths: all secured paths found in this package e.g. ['/usr/share/dbus-1/system-services/org.freedesktop.PolicyKit1.service', '/usr/share/dbus-1/system.d/org.freedesktop.PolicyKit1.conf']
        """
        # Find all digest whitelisted paths that belong to group_type and focus on current package
        digests = []
        for digest_group in self.digest_groups:
            if digest_group['type'] == group_type and self._matches_pkg(digest_group, pkg):
                digests.extend(digest_group['digests'])

        # For all files in this package that fall into the secured paths: check if they are whitelisted
        # If not whitelisted print error: file-unauthorized
        whitelisted_paths = {dg['path'] for dg in digests}
        for spath in secured_paths:
            for wpath in whitelisted_paths:
                # filepath is whitelisted
                if self._check_paths_match(spath, wpath):
                    break
            else:
                digest_hint = self._get_digest_hint(pkg, spath)
                self.output.add_info('E', pkg, f'{group_type}-file-unauthorized', spath, f'({digest_hint})')

        # For all digest whitelisted files check if the digests in the package are correct
        # If not correct print error: file-digest-mismatch
        for path in whitelisted_paths:
            # Find all digests with same path
            # This is needed because there could be an older and a newer
            # version of this package with same whitelisted paths and different digests
            digests_of_path = []
            for digest in digests:
                if self._check_paths_match(path, digest['path']):
                    digests_of_path.append(digest)
            # If *any* digest with the same path matches the package's file
            # digest of that path, then we assume the file is correctly whitelisted
            error_digests = []
            for digest in digests_of_path:
                # Check if digest whitelist path has a matching file in our package
                if not pkg.files.get(path):
                    # This digest entry is not needed anymore and could be dropped
                    continue
                try:
                    valid_digest, file_digest = self._is_valid_digest(path, digest, pkg)
                except Exception as e:
                    self.output.add_info('E', pkg, f'{group_type}-file-parse-error', path, f'failed to calculate digest: {e}')
                    continue
                if valid_digest:
                    # Valid digest found, no mismatch error will be printed
                    error_digests = []
                    break
                # Gather all digest mismatches for error message
                if file_digest:
                    error_digests.append(digest)
            if error_digests:
                for digest in error_digests:
                    digest_algorithm = digest['algorithm']
                    digest_hash = digest['hash']
                    self.output.add_info('E', pkg, f'{group_type}-file-digest-mismatch', path,
                                         f'expected {digest_algorithm}:{digest_hash}, has:{file_digest}')

    def _check_ghost_exceptions(self, pkg, name):
        """ Check if a ghosted file is whilelisted

        In general we don't allow files we want to secure to be included as %ghost. And of course there are exceptions,
        e.g. polkit-default-privs

        Params:
        - pkg: name of the package
        - name: paths of the ghosted file
        """
        for ghost_exception in self.ghost_file_exceptions:
            if not self._matches_pkg(ghost_exception, pkg):
                continue
            if name in ghost_exception['paths']:
                return True
        return False

    def _check_symlink_exceptions(self, pkg, name):
        """ Check if a symlink'ed file is in the exception list

        For some checks we generally don't want to support symlinks at all,
        but certain corner cases make it necessary to ignore certain
        package/path combinations. For these cases a separate exception list
        is maintained.
        """

        for symlink_exception in self.symlink_exceptions:
            if self._matches_pkg(symlink_exception, pkg):
                continue
            if name in symlink_exception['paths']:
                return True
        return False

    def check_binary(self, pkg):
        """
        Check that all files in secured locations are covered by a file digest group
        in which all files have valid digest.
        """

        # Find all files in this package that fall in a digest secured path
        secured_paths = {}
        for pkgfile in pkg.files.values():
            group = self._get_digest_configuration_group(pkgfile)

            if not group:
                continue
            elif pkgfile.name in pkg.ghost_files:
                if not self._check_ghost_exceptions(pkg, pkgfile.name):
                    self.output.add_info('E', pkg, f'{group}-file-ghost', pkgfile.name)
            elif stat.S_ISLNK(pkgfile.mode) and not self.follow_symlinks_in_group[group]:
                if not self._check_symlink_exceptions(pkg, pkgfile.name):
                    self.output.add_info('E', pkg, f'{group}-file-symlink', pkgfile.name)
            else:
                file_list = secured_paths.setdefault(group, [])
                file_list.append(pkgfile.name)

        # Check all found secured files for every group type
        for group, files in secured_paths.items():
            self._check_group_type(pkg, group, set(files))
