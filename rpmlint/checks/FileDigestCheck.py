import hashlib
from pathlib import Path
import stat

from rpmlint.checks.AbstractCheck import AbstractCheck


class FileDigestCheck(AbstractCheck):
    def __init__(self, config, output):
        super().__init__(config, output)
        self.digest_configurations = {}
        self.follow_symlinks_in_group = {}
        for group, values in self.config.configuration['FileDigestLocation'].items():
            self.digest_configurations[group] = [Path(p) for p in values['Locations']]
            self.follow_symlinks_in_group[group] = values['FollowSymlinks']

        self.digest_groups = self.config.configuration['FileDigestGroup']
        for digest_group in self.digest_groups:
            dg_type = digest_group['type']
            if dg_type not in self.digest_configurations:
                raise KeyError(f'FileDigestGroup type "{dg_type}" is not '
                               f'supported, known values: {list(self.digest_configurations)}')
            # expand skip digests
            for skip_digest in digest_group.get('nodigests', []):
                if not digest_group.get('digests'):
                    digest_group['digests'] = []
                digest_group['digests'].append(
                    {
                        'path': skip_digest,
                        'algorithm': 'skip',
                        'hash': '',
                    }
                )
            # verify digest algorithm
            for digest in digest_group['digests']:
                algorithm = digest['algorithm']
                if algorithm == 'skip':
                    pass
                else:
                    hashlib.new(algorithm)
        self.digest_cache = {}

    def _get_digest_configuration_group(self, pkgfile):
        if stat.S_ISDIR(pkgfile.mode):
            return None

        path = Path(pkgfile.name)
        for group, locations in self.digest_configurations.items():
            for location in locations:
                try:
                    if path.relative_to(location):
                        return group
                except ValueError:
                    pass
        return None

    def _check_filetypes(self, pkg):
        """
        Check that all symlinks point to a correct location and that
        symlinks are allowed in a configuration group.
        """
        result = True
        for filename, pkgfile in pkg.files.items():
            group = self._get_digest_configuration_group(pkgfile)
            if not group:
                continue

            if filename in pkg.ghost_files:
                self.output.add_info('E', pkg, f'{group}-file-digest-ghost', filename)
                result = False
                continue

            if stat.S_ISLNK(pkgfile.mode) and not self.follow_symlinks_in_group[group]:
                self.output.add_info('E', pkg, f'{group}-file-symlink', filename)
                result = False
                continue
        return result

    def _is_valid_digest(self, pkgfile, digest, pkg):
        algorithm = digest['algorithm']
        if algorithm == 'skip':
            return (True, None)

        while stat.S_ISLNK(pkgfile.mode):
            pkgfile = pkg.readlink(pkgfile)
            if not pkgfile:
                return (False, None)

        digest_hash = digest['hash']
        pair = (pkgfile.name, algorithm)
        if pair not in self.digest_cache:
            h = hashlib.new(algorithm)
            with open(pkgfile.path, 'rb') as fd:
                while True:
                    chunk = fd.read(4096)
                    if not chunk:
                        break
                    h.update(chunk)
            self.digest_cache[pair] = h.hexdigest()

        file_digest = self.digest_cache[pair]
        return (file_digest == digest_hash, file_digest)

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
            if digest_group['type'] == group_type and digest_group['package'] == pkg.name:
                digests.extend(digest_group['digests'])

        # For all files in this package that fall into the secured paths: check if they are whitelisted
        # If not whitelisted print error: file-digest-unauthorized
        whitelisted_paths = {dg['path'] for dg in digests}
        unauthorized = secured_paths - whitelisted_paths
        for filename in unauthorized:
            self.output.add_info('E', pkg, f'{group_type}-file-digest-unauthorized', filename, None)

        # For all digest whitelisted files check if the digests in the package are correct
        # If not correct print error: file-digest-mismatch
        for path in whitelisted_paths:
            # Find all digests with same path
            # This is needed because there could be an older and a newer
            # version of this package with same whitelisted paths and different digests
            digests_of_path = []
            for digest in digests:
                if digest['path'] == path:
                    digests_of_path.append(digest)
            # If *any* digest with the same path matches the package's file
            # digest of that path, then we assume the file is correctly whitelisted
            error_digests = []
            for digest in digests_of_path:
                filename = digest['path']
                # Check if digest whitelist path has a matching file in our package
                if not pkg.files.get(filename):
                    # This digest entry is not needed anymore and could be dropped
                    continue
                valid_digest, file_digest = self._is_valid_digest(pkg.files[filename], digest, pkg)
                if valid_digest:
                    # Valid digest found, no mismatch error will be printed
                    error_digests = []
                    break
                # Gather all digest mismatches for error message
                if file_digest:
                    error_digests.append(digest)
            if error_digests:
                for digest in error_digests:
                    self.output.add_info('E', pkg, f'{group_type}-file-digest-mismatch', filename, f'expected {digest["algorithm"]}:{digest["hash"]}, has:{file_digest}')

    def check_binary(self, pkg):
        """
        Check that all files in secured locations are covered by a file digest group
        in which all files have valid digest.
        """

        if not self._check_filetypes(pkg):
            return

        # Find all files in this package that fall in a digest secured path
        secured_paths = {}
        for pkgfile in pkg.files.values():
            group_type = self._get_digest_configuration_group(pkgfile)
            if group_type:
                secured_paths.setdefault(group_type, [])
                secured_paths[group_type].append(pkgfile.name)

        # Check all found secured files for every group type
        for group_type, files in secured_paths.items():
            self._check_group_type(pkg, group_type, set(files))
