"""
File          : CheckSUIDPermissions.py
Package       : rpmlint
Author        : Ludwig Nussel
Purpose       : Check for /usr/share/permissions violations
"""

import os
import stat
import sys

import rpm
from rpmlint.checks.AbstractCheck import AbstractCheck
from rpmlint.pkg import FakePkg


class SUIDCheck(AbstractCheck):
    def __init__(self, config, output):
        super().__init__(config, output)

        self.permissions_d_allowed = config.configuration['SUIDAllowedPermissions']
        self.perms = {}

        for fname in self._paths_to('permissions', 'permissions.secure'):
            if os.path.exists(fname):
                self._parsefile(fname)

    @staticmethod
    def _paths_to(*file_names):
        # we used to store the permissions data in /etc even though they aren't configuration files
        # the allow listing should check both paths (old /etc and new /usr/share) until all
        # distributions using the old one (SLE15) are retired
        for name in file_names:
            # return the new path first.
            # chkstat prefers the new paths over the old ones, so callers that only care about the
            # first matching file must mimic that.
            yield '/usr/share/permissions/' + name
            yield '/etc/' + name

    def _parsefile(self, fname):
        lastfn = None
        with open(fname) as inputfile:
            for lnr, line in enumerate(inputfile, start=1):
                line = line.split('#')[0].strip()
                if not line:
                    continue

                if line.startswith('+capabilities '):
                    line = line[len('+capabilities '):]
                    if lastfn:
                        self.perms[lastfn]['fscaps'] = line
                    continue

                line = line.split()
                if len(line) == 3:
                    fn = line[0]
                    owner = line[1].replace('.', ':')
                    mode = line[2]

                    self.perms[fn] = {'owner': owner, 'mode': stat.S_IMODE(int(mode, 8))}
                    # for permissions that don't change and therefore
                    # don't need special handling
                    if fname in self._paths_to('permissions'):
                        self.perms[fn]['static'] = True

                    lastfn = fn
                else:
                    lastfn = None
                    print(f'{fname}: Malformatted line {lnr}: {" ".join(line)}...', file=sys.stderr)

    def check_binary(self, pkg):
        permfiles = set()
        # first pass, find permissions.d files and check against allow list
        for f, finfo in pkg.files.items():
            for prefix in self._paths_to('permissions.d/'):
                if f.startswith(prefix):
                    if finfo.is_ghost:
                        self.output.add_info('E', pkg, 'permissions-ghostfile', f)
                        continue

                    bn = f[len(prefix):]
                    if bn not in self.permissions_d_allowed:
                        self.output.add_info('E', pkg, 'permissions-unauthorized-file', f)

                    bn = 'permissions.d/' + bn.split('.')[0]
                    permfiles.add(bn)

        # parse found permissions.d files
        for f in permfiles:
            # check for a .secure file first, falling back to the plain file
            for path in self._paths_to(f + '.secure', f):
                if path in pkg.files:
                    self._parsefile(pkg.dirName() + path)
                    break

        need_set_permissions = False
        # second pass, find permissions violations
        for f, pkgfile in pkg.files.items():

            if pkgfile.filecaps:
                self.output.add_info('E', pkg, 'permissions-fscaps', f'{f} has fscaps "{pkgfile.filecaps}"')

            mode = pkgfile.mode
            owner = pkgfile.user + ':' + pkgfile.group

            need_verifyscript = False
            if f in self.perms or (stat.S_ISDIR(mode) and f + '/' in self.perms):
                if stat.S_ISLNK(mode):
                    self.output.add_info('W', pkg, 'permissions-symlink', f)
                    continue

                need_verifyscript = True

                if stat.S_ISDIR(mode):
                    if f in self.perms:
                        self.output.add_info('W', pkg, 'permissions-dir-without-slash', f)
                    else:
                        f += '/'

                if stat.S_ISREG(mode) and mode & (stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH):
                    # pie binaries have 'shared object' here
                    if (pkgfile.magic.startswith('ELF ') and
                            ('shared object' not in pkgfile.magic) and
                            ('pie executable' not in pkgfile.magic)):
                        # TODO: not sure how much sense it makes to duplicate this check here
                        # (there's also many other compilation options we *could* check)
                        self.output.add_info('E', pkg, 'non-position-independent-executable', f)

                m = self.perms[f]['mode']
                o = self.perms[f]['owner']

                if stat.S_IMODE(mode) != m:
                    self.output.add_info('E', pkg, 'permissions-incorrect',
                                         f'{f} has mode {oct(stat.S_IMODE(mode))} but should be {oct(m)}')

                if owner != o:
                    self.output.add_info('E', pkg, 'permissions-incorrect-owner',
                                         f'{f} belongs to {owner} but should be {o}')

            elif not stat.S_ISLNK(mode):
                if f + '/' in self.perms:
                    self.output.add_info('W', pkg, 'permissions-file-as-dir',
                                         f + ' is a file but listed as directory')

                if mode & (stat.S_ISUID | stat.S_ISGID):

                    need_verifyscript = True
                    msg = '%(file)s is packaged with ' \
                          'setuid/setgid bits (0%(mode)o)' % \
                          {'file': f, 'mode': stat.S_IMODE(mode)}
                    if not stat.S_ISDIR(mode):
                        self.output.add_info('E', pkg, 'permissions-file-setuid-bit', msg)
                    else:
                        self.output.add_info('W', pkg, 'permissions-directory-setuid-bit', msg)

                    if stat.S_ISREG(mode):
                        if 'shared object' not in pkgfile.magic and 'pie executable' not in pkgfile.magic:
                            self.output.add_info('E', pkg, 'non-position-independent-executable', f)

                if mode & stat.S_IWOTH:
                    need_verifyscript = True
                    self.output.add_info('E', pkg, 'permissions-world-writable',
                                         f'{f} is packaged with world writable permissions ({oct(mode)})')

            script = not isinstance(pkg, FakePkg) and (pkg[rpm.RPMTAG_POSTIN] or pkg.scriptprog(rpm.RPMTAG_POSTINPROG))
            found = False
            if script:
                for line in script.split('\n'):
                    if 'chkstat -n' in line and f in line:
                        found = True
                        break

            if need_verifyscript and \
                    (f not in self.perms or 'static' not in self.perms[f]):

                if not script or not found:
                    self.output.add_info('E', pkg, 'permissions-missing-postin',
                                         f'missing %set_permissions {f} in %post')

                need_set_permissions = True
                script = pkg[rpm.RPMTAG_VERIFYSCRIPT] or pkg[rpm.RPMTAG_VERIFYSCRIPTPROG]

                found = False
                if script:
                    for line in script.split('\n'):
                        if '/chkstat' in line and f in line:
                            found = True
                            break

                if not script or not found:
                    self.output.add_info('W', pkg, 'permissions-missing-verifyscript',
                                         f'missing %verify_permissions -e {f}')

        if need_set_permissions:
            if 'permissions' not in (x[0] for x in pkg.prereq):
                self.output.add_info('E', pkg, 'permissions-missing-requires',
                                     "missing 'permissions' in Requires(phase)")
