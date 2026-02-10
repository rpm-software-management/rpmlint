import os
import stat

import rpm
from rpmlint.checks.AbstractCheck import AbstractCheck
from rpmlint.permissions import PermissionsParser, VariablesHandler

SHARE_DIR = '/usr/share/permissions'


class SUIDPermissionsCheck(AbstractCheck):
    """Restrict installation of files with special privileges (set*id bits,
    capabilities)."""

    def __init__(self, config, output):
        super().__init__(config, output)
        # maps normalized paths (without trailing slash) to a list of [PermissionsEntry]
        #
        # the list values are necessary since multiple entries can exist for
        # the same path, tied to different packages (or tied to no package at
        # all).
        self.perms = {}
        self.var_handler = VariablesHandler(f'{SHARE_DIR}/variables.conf')

        # parse the central permissions profiles: the static configuration and
        # the secure profile. The latter is the reference profile decisions
        # are based on in _verify_entry().
        for fname in self._paths_to('permissions', 'permissions.secure'):
            if not os.path.exists(fname):
                continue

            self._parse_profile(fname)

    def _parse_profile(self, path):
        parser = PermissionsParser(self.var_handler, path)
        self.perms.update(parser.entries)

    def _complain_restricted_mode(self, pkg, path, mode):
        msg = f'{path} is packaged with setuid/setgid bits (0{stat.S_IMODE(mode):o})'
        diag = 'permissions-directory-setuid-bit' if stat.S_ISDIR(mode) else 'permissions-file-setuid-bit'
        self.output.add_info('E', pkg, diag, msg)

    def _verify_entry(self, entry, pkg, path, rpm_mode, rpm_owner):
        """Complains about disagreements between the package metadata and the
        permissions profile settings. We also require the RPM permissions to
        match the reference permissions profile (secure)."""
        is_listed_as_dir = entry.path.endswith('/')
        is_packaged_as_dir = stat.S_ISDIR(rpm_mode)

        if is_packaged_as_dir and not is_listed_as_dir:
            self.output.add_info('W', pkg, 'permissions-dir-without-slash', path)
        elif is_listed_as_dir and not is_packaged_as_dir:
            self.output.add_info('W', pkg, 'permissions-file-as-dir', f'{path} is a file but listed as directory')

        entry_owner = ':'.join((entry.owner, entry.group))

        if stat.S_IMODE(rpm_mode) != entry.mode:
            self.output.add_info('E', pkg, 'permissions-incorrect', f'{path} has mode 0{stat.S_IMODE(rpm_mode):o} but should be 0{entry.mode:o}')

        if rpm_owner != entry_owner:
            self.output.add_info('E', pkg, 'permissions-incorrect-owner', f'{path} belongs to {rpm_owner} but should be {entry_owner}')

    def _check_post_scriptlets(self, pkg, path):
        """Checks whether a call to "permctl -n {path}" is found in %post and
        %verifyscript scriptlets of the package and complains if this is not
        the case."""
        found_postin = self._lookup_permctl_call(path, pkg[rpm.RPMTAG_POSTIN] or pkg.scriptprog(rpm.RPMTAG_POSTINPROG))
        found_verify = self._lookup_permctl_call(path, pkg[rpm.RPMTAG_VERIFYSCRIPT] or pkg[rpm.RPMTAG_VERIFYSCRIPTPROG])

        if not found_postin:
            self.output.add_info('E', pkg, 'permissions-missing-postin', f'missing %set_permissions {path} in %post')

        if not found_verify:
            self.output.add_info('W', pkg, 'permissions-missing-verifyscript', f'missing %verify_permissions -e {path}')

    def _lookup_permctl_call(self, path, script):
        """Checks whether a call to "permctl -n {path}" is present in the
        given `script`."""
        import re

        if not script:
            return False

        escaped = re.escape(path)

        for line in script.splitlines():
            if re.search(fr'(chkstat|permctl) -n .* {escaped}', line):
                return True

        return False

    @staticmethod
    def _paths_to(*file_names):
        # we used to store the permissions data in /etc even though they aren't configuration files
        # the whitelisting should check both paths (old /etc and new /usr/share) until all
        # distributions using the old one (SLE15) are retired
        for name in file_names:
            # return the new path first.
            # chkstat prefers the new paths over the old ones, so callers that only care about the
            # first matching file must mimic that.
            yield f'{SHARE_DIR}/{name}'
            yield f'/etc/{name}'

    def _is_static_entry(self, pkg, path):
        for entry in self.perms.get(path, []):
            if entry.matches_pkg(pkg.name) and entry.is_static():
                return True

        return False

    def check(self, pkg):
        if pkg.is_source:
            return

        dropin_files = set()
        # first pass: find and parse per-package drop-in files, these take
        # priority over the central profiles parsed in the constructor.
        for f in pkg.files.keys():
            for prefix in list(self._paths_to('permissions.d/')) + [f'{SHARE_DIR}/packages.d/']:
                if not f.startswith(prefix):
                    continue
                elif f in pkg.ghost_files:
                    continue

                dropin_dir = os.path.basename(prefix.rstrip('/'))

                # these drop-in configuration files are whitelisted separately
                # via permissions-whitelist.toml and are thus considered
                # trusted.

                # we only add the basename of the drop-in configuration file
                # without suffix. Below we'll lookup the .secure variant
                # first, if existing, otherwise the basename.
                bn = f'{dropin_dir}/' + f[len(prefix):].split('.')[0]
                dropin_files.add(bn)

        for f in dropin_files:
            # check for a .secure file first, falling back to the plain file
            for path in self._paths_to(f + '.secure', f):
                if path in pkg.files:
                    # this path points to the extracted package directory tree
                    fullpath = pkg.dir_name() + path
                    try:
                        self._parse_profile(fullpath)
                    except Exception as e:
                        self.output.add_info('E', pkg, 'permissions-parse-error', f'{fullpath} caused a parsing error: {str(e)}.')
                    break

        # whether a PreReq for the permissions package will be needed in this RPM
        requires_permctl = False

        for f, pkgfile in pkg.files.items():
            if pkgfile.is_ghost:
                # We want to skip ghost files here. The package is not
                # actually shipping the file and we allow e.g. tmpfilesd to
                # create entries with special permissions. If we would warn
                # about these entries, rpm -v would show errors. The drawback
                # is that that we don't see warnings for privileges added by
                # other mechanisms that are described in these %ghost files
                continue
            if pkgfile.filecaps:
                # capabilities are only assigned via permctl, should not be
                # packaged directly
                self.output.add_info('E', pkg, 'permissions-fscaps', f"{f} has fscaps '{pkgfile.filecaps}'")

            mode = pkgfile.mode
            owner = pkgfile.user + ':' + pkgfile.group
            # whether we need to check for invocation of permctl in %post or
            # %verifyscript for this path
            check_scriptlets = False

            skip_file = False
            for entry in self.perms.get(f, []):
                if entry.matches_pkg(pkg.name):
                    if stat.S_ISLNK(mode):
                        self.output.add_info('W', pkg, 'permissions-symlink', f)
                        skip_file = True
                        break

                    check_scriptlets = True
                    self._verify_entry(entry, pkg, f, mode, owner)
                    break
            else:
                # no matching entry found; this means there is no whitelisting for any privileged bits.
                if not stat.S_ISLNK(mode) and (mode & (stat.S_ISUID | stat.S_ISGID)):
                    check_scriptlets = True
                    self._complain_restricted_mode(pkg, f, mode)

            if skip_file:
                # is a symlink we warned about
                continue

            if check_scriptlets:
                # don't care about "static" entries that only serve a whitelisting
                # purpose (e.g. directory sticky bits) or as a sanity check (e.g. safe
                # permissions for /etc/ssh*).
                # These permissions should already be correct after RPM install,
                # so a call to permctl during %post is not strictly necessary.
                if not self._is_static_entry(pkg, f):
                    self._check_post_scriptlets(pkg, f)
                    requires_permctl = True

        if requires_permctl:
            if 'permissions' not in [x[0] for x in pkg.prereq]:
                self.output.add_info('E', pkg, 'permissions-missing-requires', "missing 'permissions' in PreReq")
