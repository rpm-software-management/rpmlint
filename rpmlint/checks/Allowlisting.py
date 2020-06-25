#############################################################################
# Author        : Matthias Gerstner
# Purpose       : reusable code for dealing with security allow lists
#############################################################################

import abc
from dataclasses import make_dataclass
import hashlib
import json
import os
import os.path
import sys
import traceback

from rpmlint.checks.AbstractCheck import AbstractCheck


class DigestVerificationResult(make_dataclass('', ['path', 'algorithm', 'expected', 'encountered'])):
    """This type represents the result of a digest verification as returned
    from AuditEntry.compare_digests()."""

    def matches(self):
        """Returns a boolean whether the encountered digest matches the
        expected digest."""
        return self.expected == self.encountered


class AuditEntry:
    """This object represents a single audit entry as found in an allow entry like:

    "bsc#1234": {
        "comment": "some comment",
        "digests": {
            "/some/file": "<alg>:<digest>",
            ...
        }
    }

    """

    def __init__(self, bug):
        self.bug = bug
        self._verify_bug_nr()
        self.comment = ''
        self.digests = {}

    def _set_digests(self, digests):
        for path, digest in digests.items():
            self._verify_path(path)
            self._verify_digest_syntax(digest)

        self.digests = digests

    @staticmethod
    def is_skip_digest(digest):
        """Returns whether the given digest entry denotes the special 'skip
        digest' case which means not to check the file digest at all."""
        return digest == 'skip:<none>'

    def covers_all_files(self, file_paths):
        """Returns a boolean indicating whether all files from the set
        'file_paths' are covered by this audit."""
        return file_paths.issubset(self.digests.keys())

    def compare_digests(self, pkg):
        """Compares the digests recorded in this AuditEntry against the actual
        files coming from the given rpmlint @pkg. Returns a tuple of
        (boolean, [DigestVerificationResult, ...]). The boolean indicates the
        overall verification result, while the list of
        DigestVerificationResult entries provides detailed information about
        the encountered data. Any 'skip digest' entries will be ignored and
        not be included in the result list."""

        results = []

        # NOTE: syntax and algorithm validity of stored digests was already
        # checked in _set_digests() so we can skip the respective error handling
        # here.

        fileinfos = pkg.files

        for path, digest in self.digests.items():
            alg, digest = digest.split(':', 1)

            if self.is_skip_digest(f'{alg}:{digest}'):
                results.append(DigestVerificationResult(path, alg, digest, digest))
                continue

            try:
                h = hashlib.new(alg)

                src_info = fileinfos.get(path, None)

                if not src_info:
                    raise Exception(f'expected file {path} is not part of the RPM')

                # resolve potential symbolic links
                #
                # this function handles both absolute and relative symlinks
                # and does not access paths outside the RPM.
                #
                # it is not safe against symlink loops, however, it will
                # result in an infinite loop it such cases. But there are
                # probably a lot of other possibilities to DoS the RPM build
                # process or rpmlint.
                dst_info = pkg.readlink(src_info)

                if not dst_info:
                    raise Exception(f'symlink {src_info.path} -> {src_info.linkto} is broken or pointing outside this RPM')

                # NOTE: this path is dynamic, rpmlint unpacks the RPM
                # contents into a temporary directory even when outside the
                # build environment i.e. the file content should always be
                # available to us.
                with open(dst_info.path, 'rb') as fd:
                    while True:
                        chunk = fd.read(4096)
                        if not chunk:
                            break

                        h.update(chunk)

                    encountered = h.hexdigest()
            except IOError as e:
                encountered = 'error:' + str(e)
            except Exception as e:
                encountered = 'error:' + str(e)

            dig_res = DigestVerificationResult(path, alg, digest, encountered)
            results.append(dig_res)

        return all(res.matches() for res in results), results

    def _verify_bug_nr(self):
        """Perform some sanity checks on the bug nr associated with this audit
        entry."""

        parts = self.bug.split('#')

        if len(parts) != 2 or \
                parts[0] not in ('bsc', 'boo', 'bnc') or \
                not parts[1].isdigit():
            raise Exception(f'Bad bug nr# "{self.bug}"')

    def _verify_digest_syntax(self, digest):
        if self.is_skip_digest(digest):
            return

        parts = digest.split(':')
        if len(parts) != 2:
            raise Exception('Bad digest specification ' + digest)

        alg, hexdigest = parts

        try:
            hashlib.new(alg)
        except ValueError:
            raise Exception('Bad digest algorithm in ' + digest)

    def _verify_path(self, path):
        if not path.startswith(os.path.sep):
            raise Exception('Bad allow listing path ' + path)


def allowlist_for_package(allowlist_path, pkg_name):
    class AllowlistParser:
        """This type knows how to parse the JSON allow listing format. The format
        is documented in [1].

        [1]: https://github.com/openSUSE/rpmlint-security-whitelistings/blob/master/README.md
        """

        def __init__(self, wl_path):
            """Creates a new instance of AllowlistParser that operates on
            @wl_path."""

            self.path = wl_path

        def parse(self, package):
            """Parses the allow list file for the current package and returns a list of AuditEntry objects."""

            try:
                with open(self.path, 'r') as fd:
                    data = json.load(fd)

                    try:
                        config = data[package]
                    except KeyError:
                        return []

                    return self._parse_allowlist_entry(package, config)
            except Exception as e:
                _, _, tb = sys.exc_info()
                fn, ln, _, _ = traceback.extract_tb(tb)[-1]
                raise Exception(self._get_error_prefix() + f'Failed to parse JSON file: {fn}:{ln}: {e}')

        def _parse_allowlist_entry(self, package, config):
            """Parses a single JSON allow entry and returns a AuditEntry()
            object for it. On non-critical error conditions None is returned,
            otherwise an exception is raised."""

            ret = []

            audits = config.get('audits')

            if not audits:
                raise Exception(self._get_error_prefix() + f"no 'audits' entries for package {package}")

            for bug, data in audits.items():
                try:
                    audit = self._parse_audit_entry(bug, data)
                except Exception as e:
                    raise Exception(self._get_error_prefix() + 'Failed to parse audit entries: ' + str(e))

                # missing audit is soft error, continue parsing
                if audit:
                    ret.append(audit)

            return ret

        def _parse_audit_entry(self, bug, data):
            """Parses a single JSON audit sub-entry returns an AuditEntry() object
            for it. On non-critical error conditions None is returned, otherwise
            an exception is raised"""

            ret = AuditEntry(bug)

            comment = data.get('comment')
            if comment:
                ret.comment = comment

            digests = data.get('digests')

            if not digests:
                raise Exception(self._get_error_prefix() + f"no 'digests' entry for '{bug}'")

            ret._set_digests(digests)

            return ret

        def _get_error_prefix(self):
            return self.path + ': ERROR: '

    parser = AllowlistParser(allowlist_path)
    return parser.parse(pkg_name)


class AbstractAllowlistCheck(AbstractCheck, metaclass=abc.ABCMeta):
    """An abstract base class for comparing files found in an RPM against an allow list with hashed file contents."""

    def __init__(self, config, output):
        for req_key in ('unauthorized', 'changed', 'ghost'):
            assert req_key in self.error_map, f'Missing error mapping in class {type(self)}'
        super().__init__(config, output)

    @property
    @abc.abstractmethod
    def allowlist_filenames(self):
        """ The file names (an iterable of strings) which contain the allow lists to be used. """
        pass

    @property
    @abc.abstractmethod
    def restricted_paths(self):
        """ An iterable of file paths (strings) children of which must be checked against
        the allow list.
        Note: use paths ending with / in order to only catch descendants of directories but not these
        dirs themselves."""
        pass

    @property
    @abc.abstractmethod
    def error_map(self):
        """ A dictionary with keys 'unauthorized', 'changed', 'ghost' that maps these to the
        desired rpmlint error identifiers for this check. """
        pass

    def read_allowlist(self, pkg):
        """ Retrieves the allow list for a package.

        The special return value 'None' means no list is configured and all files should pass."""
        # this option is found in config files in /opt/testing/share/rpmlint/mini,
        # installed there by the rpmlint-mini package.
        allowlist_dir = self.config.configuration.get('WhitelistDataDir', [])

        if not self.allowlist_filenames:
            return None

        rules_entries = []
        for filename in self.allowlist_filenames:
            for wd in allowlist_dir:
                candidate = os.path.join(wd, filename)
                if os.path.exists(candidate):
                    rules_entries += allowlist_for_package(candidate, pkg.name)
                    break

        return rules_entries

    def collect_restricted_files(self, pkg):
        """ Collects the set of files that are restricted and need to be in the allowed list. """

        def is_restricted(f):
            return any(f.startswith(restricted) for restricted in self.restricted_paths)
        return {f for f in pkg.files.keys() if is_restricted(f)}

    def check_binary(self, pkg):
        restricted_files = self.collect_restricted_files(pkg)

        for f in restricted_files & set(pkg.ghost_files):
            self.output.add_info('E', pkg, self.error_map['ghost'], f)
            restricted_files.remove(f)

        if not restricted_files:
            return

        results = []

        # don't ruin the whole run if this check is not configured, this
        # was hopefully intended by the user.
        allow_list = self.read_allowlist(pkg)
        if allow_list is None:
            return

        for audit in allow_list:
            digest_matches, results = audit.compare_digests(pkg)

            if digest_matches and audit.covers_all_files(restricted_files):
                break
        else:
            # print the encountered and expected digests and paths for diagnostic purposes
            for result in results:
                restricted_files -= {result.path}

                if result.matches():
                    continue

                print(f'{result.path}: expected {result.algorithm} digest {result.expected} but encountered {result.encountered}', file=sys.stderr)
                self.output.add_info('E', pkg, self.error_map['changed'], result.path)

            for f in restricted_files:
                self.output.add_info('E', pkg, self.error_map['unauthorized'], f)


class AbstractSimpleAllowlistCheck(AbstractCheck, metaclass=abc.ABCMeta):
    """An abstract base class for comparing files found in an RPM against a
    simple list from the configuration with allowed file names in a directory."""

    @property
    @abc.abstractmethod
    def allowlist_config_key(self):
        """ The config key (a string) under which all allowed file names are stored. """
        pass

    @property
    @abc.abstractmethod
    def restricted_paths(self):
        """ An iterable of file paths (strings) children of which must be checked against
        the allow list.
        Note: use paths ending with / in order to only catch descendants of directories but not these
        dirs themselves."""
        pass

    @property
    @abc.abstractmethod
    def error_map(self):
        """ A dictionary with keys 'unauthorized', 'ghost' that maps these to the
        desired rpmlint error identifiers for this check. """
        pass

    def check_binary(self, pkg):
        """Checks that files in polkit-default-privs.d are on an allow list."""
        allowed_filenames = self.config.configuration.get(self.allowlist_config_key, ())

        for filename, fileinfo in pkg.files.items():
            for dir_name in self.restricted_paths:
                if filename.startswith(dir_name):
                    bn = filename[len(dir_name):]
                    break
            else:
                continue
            print(repr(filename), file=sys.stderr)

            if fileinfo.is_ghost:
                self.output.add_info('E', pkg, self.error_map['ghost'], filename)
            elif bn not in allowed_filenames:
                self.output.add_info('E', pkg, self.error_map['unauthorized'], filename)
