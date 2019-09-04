import fnmatch
from pathlib import Path
import re

from rpm import RPMTAG_VENDOR
from rpmlint.checks.AbstractCheck import AbstractCheck
from rpmlint.helpers import byte_to_string
import toml


class FilelistCheck(AbstractCheck):
    @staticmethod
    def notnoarch(pkg):
        return pkg.arch != 'noarch'

    @staticmethod
    def isfilesystem(pkg):
        return pkg.name == 'filesystem'

    @staticmethod
    def isdebuginfo(pkg):
        return (pkg.name.endswith('-debuginfo') or
                pkg.name.endswith('-debuginfo-32bit') or
                pkg.name.endswith('-debuginfo-64bit') or
                pkg.name.endswith('-debugsource') or pkg.name.endswith('-debug'))

    @staticmethod
    def notsymlink(pkg, f):
        file_mode = pkg.files[f].mode
        file_type = (file_mode >> 12) & 0o17
        return file_type != 0o12

    @staticmethod
    def ghostfile(pkg, f):
        ghosts = pkg.ghost_files
        return f in ghosts

    def __init__(self, config, output):
        super().__init__(config, output)

        # computed from goodprefixes.
        # Directories that are only allowed to have defined subdirs (such as /usr)
        self._restricteddirs = set()
        self._restricteddirs.add('/')

        config = toml.load(Path(__file__).parent / 'FilelistCheck.toml')
        self.goodprefixes = tuple(config['GoodPrefixes'])
        self.checks = config['Check']

        for d in self.goodprefixes:
            if d.count('/') > 2:
                self._restricteddirs.add(d[0:-1].rpartition('/')[0])

        for check in self.checks:
            if 'Good' in check:
                for i in range(len(check['Good'])):
                    pattern = check['Good'][i]
                    if '*' in pattern:
                        r = fnmatch.translate(pattern)
                        check['Good'][i] = re.compile(r)

            if 'Bad' in check:
                for i in range(len(check['Bad'])):
                    pattern = check['Bad'][i]
                    if '*' in pattern:
                        r = fnmatch.translate(pattern)
                        check['Bad'][i] = re.compile(r)

    def check(self, pkg):
        if pkg.is_source:
            return

        files = pkg.files
        for check in self.checks:
            if 'IgnorePkgIf' in check:
                if getattr(self, check['IgnorePkgIf'])(pkg):
                    continue

            if 'Good' in check or 'Bad' in check:
                for f in files:
                    ok = False
                    if 'Good' in check:
                        for g in check['Good']:
                            if ((not isinstance(g, str) and g.match(f)) or
                                    g == f):
                                ok = True
                                break
                    if ok:
                        continue

                    if 'Bad' in check:
                        for b in check['Bad']:
                            if 'IgnoreFileIf' in check:
                                if getattr(self, check['IgnoreFileIf'])(pkg, f):
                                    continue
                            if ((not isinstance(b, str) and b.match(f)) or
                                    b == f):
                                self.output.add_info('E', pkg, check['Message'], f)

        invalidfhs = set()
        invalidopt = set()

        is_suse = (pkg.header[RPMTAG_VENDOR] and 'SUSE' in byte_to_string(pkg.header[RPMTAG_VENDOR]))

        # the checks here only warn about a directory once rather
        # than reporting potentially hundreds of files individually
        for f, pkgfile in files.items():
            file_type = (pkgfile.mode >> 12) & 0o17

            # append / to directories
            if file_type == 4:
                f += '/'

            if not f.startswith(self.goodprefixes):
                base = f.rpartition('/')
                pfx = None
                # find the first invalid path component
                # (/usr/foo/bar/baz -> /usr)
                while (base[0] and not base[0].startswith(self.goodprefixes) and
                       not base[0] in self._restricteddirs):
                    pfx = base[0]
                    base = base[0].rpartition('/')

                if not pfx:
                    invalidfhs.add(f)
                else:
                    invalidfhs.add(pfx)

            if f.startswith('/opt'):
                try:
                    provider = f.split('/')[2]
                except Exception:
                    continue
                if is_suse and (provider == 'suse' or provider == 'novell'):
                    continue

                d = '/opt/' + provider
                invalidopt.add(d)

        for f in invalidfhs:
            self.output.add_info('E', pkg, 'filelist-forbidden-fhs23', f)

        for f in invalidopt:
            self.output.add_info('E', pkg, 'filelist-forbidden-opt', f)
