import os
import stat

import rpm
from rpmlint.checks.AbstractCheck import AbstractCheck
from rpmlint.permissions import PermissionsParser, VariablesHandler


class SUIDPermissionsCheck(AbstractCheck):
    def __init__(self, config, output):
        super().__init__(config, output)
        self.perms = {}

        self.var_handler = VariablesHandler('/usr/share/permissions/variables.conf')

        for fname in self._paths_to('permissions', 'permissions.secure'):
            if not os.path.exists(fname):
                continue

            self._parse_profile(fname)

    def _parse_profile(self, path):
        parser = PermissionsParser(self.var_handler, path)
        self.perms.update(parser.entries)

    def _check_restricted_mode(self, pkg, path, mode):
        msg = f'{path} is packaged with setuid/setgid bits (0{stat.S_IMODE(mode):o})'
        if not stat.S_ISDIR(mode):
            self.output.add_info('E', pkg, 'permissions-file-setuid-bit', msg)
        else:
            self.output.add_info('E', pkg, 'permissions-directory-setuid-bit', msg)

    def _verify_entry(self, pkg, path, mode, owner):
        entry = self.perms[path]

        is_listed_as_dir = entry.path.endswith('/')
        is_packaged_as_dir = stat.S_ISDIR(mode)

        if is_packaged_as_dir and not is_listed_as_dir:
            self.output.add_info('W', pkg, 'permissions-dir-without-slash', path)
        elif is_listed_as_dir and not is_packaged_as_dir:
            self.output.add_info('W', pkg, 'permissions-file-as-dir', f'{path} is a file but listed as directory')

        m = entry.mode
        o = ':'.join((entry.owner, entry.group))

        if stat.S_IMODE(mode) != m:
            self.output.add_info('E', pkg, 'permissions-incorrect', f'{path} has mode 0{stat.S_IMODE(mode):o} but should be 0{m:o}')

        if owner != o:
            self.output.add_info('E', pkg, 'permissions-incorrect-owner', f'{path} belongs to {owner} but should be {o}')

    def _check_post_scriptlets(self, pkg, path, need_verifyscript):
        script = pkg[rpm.RPMTAG_POSTIN] or pkg.scriptprog(rpm.RPMTAG_POSTINPROG)
        found = False
        need_set_permissions = False

        if script:
            for line in script.split('\n'):
                if 'chkstat -n' in line and path in line:
                    found = True
                    break

        # don't care about "static" entries that only serve as a kind of
        # whitelisting purpose or sanity check that should only be applied
        # during `chkstat --system`
        if path in self.perms and self._is_static_entry(self.perms[path]):
            return False

        if need_verifyscript:
            if not script or not found:
                self.output.add_info('E', pkg, 'permissions-missing-postin', f'missing %set_permissions {path} in %post')

            need_set_permissions = True
            script = (pkg[rpm.RPMTAG_VERIFYSCRIPT] or pkg[rpm.RPMTAG_VERIFYSCRIPTPROG])

            found = False
            if script:
                for line in script.split('\n'):
                    if '/chkstat' in line and path in line:
                        found = True
                        break

            if not script or not found:
                self.output.add_info('W', pkg, 'permissions-missing-verifyscript', f'missing %verify_permissions -e {path}')

        return need_set_permissions

    def _is_static_entry(self, entry):
        # entries coming from the fixed permissions profile are considered
        # static
        return entry.profile.endswith('/permissions')

    @staticmethod
    def _paths_to(*file_names):
        # we used to store the permissions data in /etc even though they aren't configuration files
        # the whitelisting should check both paths (old /etc and new /usr/share) until all
        # distributions using the old one (SLE15) are retired
        for name in file_names:
            # return the new path first.
            # chkstat prefers the new paths over the old ones, so callers that only care about the
            # first matching file must mimic that.
            yield '/usr/share/permissions/' + name
            yield '/etc/' + name

    def check(self, pkg):
        if pkg.is_source:
            return

        permfiles = set()
        # first pass, find and parse permissions.d files
        for f in pkg.files.keys():
            for prefix in self._paths_to('permissions.d/'):
                if f.startswith(prefix):
                    if f in pkg.ghost_files:
                        continue

                    # Attention: We require the FileDigestLocation config to
                    # mark all permissions.d paths as "blacklisted" paths.
                    # e.g. [FileDigestLocation.permissions] with Locations
                    # /etc/permissions.d/ and /usr/share/permissions/permissions.d/
                    # This ensures that an file-unauthorized error is thrown when a permissions.d
                    # package is not whitelisted.
                    #
                    # To whitelist a permissions.d file after a successful review,
                    # the path and its digest need to be added as FileDigestCheck config
                    # having respective FileDigestLocation type (e.g.
                    # "permissions").
                    #
                    # Here we add *all* files in a package's permissions.d directory to our
                    # valid permissions files *without* checking if they belong
                    # to a whitelist as we assume it will be checked by
                    # FileDigestCheck and FileDigestLocation.
                    bn = 'permissions.d/' + f[len(prefix):].split('.')[0]
                    if bn not in permfiles:
                        permfiles.add(bn)

        for f in permfiles:
            # check for a .secure file first, falling back to the plain file
            for path in self._paths_to(f + '.secure', f):
                if path in pkg.files:
                    fullpath = pkg.dir_name() + path
                    try:
                        self._parse_profile(fullpath)
                    except Exception as e:
                        self.output.add_info('E', pkg, 'permissions-parse-error', f'{fullpath} caused a parsing error: {str(e)}.')
                    break

        need_set_permissions = False

        for f, pkgfile in pkg.files.items():
            if pkgfile.is_ghost:
                # if a file is ghost we want to skip the files here. It's not
                # actually shipping the file and we allow e.g. tmpfilesd to
                # create entries with special permissions. If we would warn for
                # these entries rpm -v will show errors.
                # The drawback is that that we don't see warnings for privileges
                # added by other mechanisms that are described in these %ghost
                # files
                continue
            if pkgfile.filecaps:
                self.output.add_info('E', pkg, 'permissions-fscaps', f"{f} has fscaps '{pkgfile.filecaps}'")

            mode = pkgfile.mode
            owner = pkgfile.user + ':' + pkgfile.group

            need_verifyscript = False
            if f in self.perms:
                if stat.S_ISLNK(mode):
                    self.output.add_info('W', pkg, 'permissions-symlink', f)
                    continue

                need_verifyscript = True
                self._verify_entry(pkg, f, mode, owner)

            elif not stat.S_ISLNK(mode):
                if mode & (stat.S_ISUID | stat.S_ISGID):
                    need_verifyscript = True
                    self._check_restricted_mode(pkg, f, mode)

            if self._check_post_scriptlets(pkg, f, need_verifyscript):
                need_set_permissions = True

        if need_set_permissions and 'permissions' not in [x[0] for x in pkg.prereq]:
            self.output.add_info('E', pkg, 'permissions-missing-requires', "missing 'permissions' in PreReq")
