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
        self.perms.update(parser.getEntries())

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

        need_set_permissions = False
        found_suseconfig = False

        for f, pkgfile in pkg.files.items():

            if pkgfile.filecaps:
                self.output.add_info(
                    'E',
                    pkg,
                    'permissions-fscaps',
                    "%(fname)s has fscaps '%(caps)s'"
                    % {'fname': f, 'caps': pkgfile.filecaps},
                )

            mode = pkgfile.mode
            owner = pkgfile.user + ':' + pkgfile.group

            need_verifyscript = False
            if f in self.perms or (stat.S_ISDIR(mode) and f + '/' in self.perms):
                if stat.S_ISLNK(mode):
                    self.output.add_info('W', pkg, 'permissions-symlink', f)
                    continue

                need_verifyscript = True

                m = 0
                o = 'invalid'
                if stat.S_ISDIR(mode):
                    if f in self.perms:
                        self.output.add_info(
                            'W', pkg, 'permissions-dir-without-slash', f
                        )
                    else:
                        f += '/'

                entry = self.perms[f]

                if stat.S_ISREG(mode) and mode & (
                    stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH
                ):
                    # pie binaries have 'shared object' here
                    if (
                        pkgfile.magic.startswith('ELF ') and ('shared object' not in pkgfile.magic) and ('pie executable' not in pkgfile.magic)
                    ):
                        self.output.add_info(
                            'E', pkg, 'non-position-independent-executable', f
                        )

                m = entry.mode
                o = ':'.join((entry.owner, entry.group))

                if stat.S_IMODE(mode) != m:
                    self.output.add_info(
                        'E',
                        pkg,
                        'permissions-incorrect',
                        '%(file)s has mode 0%(mode)o but should be 0%(m)o'
                        % {'file': f, 'mode': stat.S_IMODE(mode), 'm': m},
                    )

                if owner != o:
                    self.output.add_info(
                        'E',
                        pkg,
                        'permissions-incorrect-owner',
                        '%(file)s belongs to %(owner)s but should be %(o)s'
                        % {'file': f, 'owner': owner, 'o': o},
                    )

            elif not stat.S_ISLNK(mode):

                if f + '/' in self.perms:
                    self.output.add_info(
                        'W',
                        pkg,
                        'permissions-file-as-dir',
                        f + ' is a file but listed as directory',
                    )

                if mode & (stat.S_ISUID | stat.S_ISGID):
                    need_verifyscript = True
                    msg = (
                        '%(file)s is packaged with '
                        'setuid/setgid bits (0%(mode)o)'
                        % {'file': f, 'mode': stat.S_IMODE(mode)}
                    )
                    if not stat.S_ISDIR(mode):
                        self.output.add_info(
                            'E', pkg, 'permissions-file-setuid-bit', msg
                        )
                    else:
                        self.output.add_info(
                            'W', pkg, 'permissions-directory-setuid-bit', msg
                        )

                    if stat.S_ISREG(mode):
                        if (
                            'shared object' not in pkgfile.magic and 'pie executable' not in pkgfile.magic
                        ):
                            self.output.add_info(
                                'E', pkg, 'non-position-independent-executable', f
                            )

            script = pkg[rpm.RPMTAG_POSTIN] or pkg.scriptprog(rpm.RPMTAG_POSTINPROG)
            found = False
            if script:
                for line in script.split('\n'):
                    if 'chkstat -n' in line and f in line:
                        found = True
                        break

                    if (
                        'SuSEconfig --module permissions' in line or 'run_permissions is obsolete' in line
                    ):
                        found = True
                        found_suseconfig = True
                        break

            if need_verifyscript and (
                f not in self.perms or not self._is_static_entry(self.perms[f])
            ):

                if not script or not found:
                    self.output.add_info(
                        'E',
                        pkg,
                        'permissions-missing-postin',
                        'missing %%set_permissions %s in %%post' % f,
                    )

                need_set_permissions = True
                script = (
                    pkg[rpm.RPMTAG_VERIFYSCRIPT] or pkg[rpm.RPMTAG_VERIFYSCRIPTPROG]
                )

                found = False
                if script:
                    for line in script.split('\n'):
                        if '/chkstat' in line and f in line:
                            found = True
                            break

                if not script or not found:
                    self.output.add_info(
                        'W',
                        pkg,
                        'permissions-missing-verifyscript',
                        'missing %%verify_permissions -e %s' % f,
                    )

        if need_set_permissions:
            if 'permissions' not in map(lambda x: x[0], pkg.prereq):
                self.output.add_info(
                    'E',
                    pkg,
                    'permissions-missing-requires',
                    "missing 'permissions' in PreReq",
                )

        if found_suseconfig:
            self.output.add_info(
                'I',
                pkg,
                'permissions-suseconfig-obsolete',
                '%run_permissions is obsolete',
            )
