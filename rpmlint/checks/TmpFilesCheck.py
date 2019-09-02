from pathlib import Path
import re
import stat

import rpm
from rpmlint.checks.AbstractCheck import AbstractCheck


class TmpFilesCheck(AbstractCheck):
    def check(self, pkg):
        if pkg.isSource():
            return

        # file names handled by systemd-tmpfiles
        tmp_files = set()
        postin = pkg[rpm.RPMTAG_POSTIN]
        prein = pkg[rpm.RPMTAG_PREIN]

        # see tmpfiles.d(5)
        interesting_types = ('f', 'F', 'w', 'd', 'D', 'p', 'L', 'c', 'b')

        for fn, pkgfile in pkg.files().items():
            if not fn.startswith('/usr/lib/tmpfiles.d/'):
                continue
            if not stat.S_ISREG(pkgfile.mode):
                self.output.add_info('W', pkg, 'tmpfile-not-regular-file', fn)
                continue

            basename = Path(fn).name
            pattern = re.compile(
                r'systemd-tmpfiles --create .*%s' % re.escape(basename))
            if (not postin or not pattern.search(postin)) and \
                    (not prein or not pattern.search(prein)):
                self.output.add_info('W', pkg, 'postin-without-tmpfile-creation', fn)

            with open(pkgfile.path) as inputf:
                for line in inputf:
                    # skip comments
                    line = line.split('#')[0].split('\n')[0]
                    line = line.lstrip()
                    if not len(line):
                        continue
                    line = re.split(r'\s+', line)
                    # format is
                    # Type Path        Mode UID  GID  Age Argument
                    # we only need type and path
                    if len(line) < 3:
                        continue
                    t = line[0]
                    p = line[1]
                    if t.endswith('!'):
                        t = t[:-1]
                    if t not in interesting_types:
                        continue

                    tmp_files.add(p)

                    if p not in pkg.files():
                        self.output.add_info('W', pkg, 'tmpfile-not-ghost', p)

        # now check remaining ghost files that are not already
        # handled by systemd-tmpfiles
        ghost_files = set(pkg.ghostFiles()) - tmp_files
        if ghost_files:
            for f in ghost_files:
                if f in pkg.missingOkFiles():
                    continue
                if not postin and not prein:
                    self.output.add_info('W', pkg, 'ghost-files-without-postin')
                if (not postin or f not in postin) and \
                        (not prein or f not in prein):
                    self.output.add_info('W', pkg, 'postin-without-ghost-file-creation', f)
