import re

from rpmlint.checks.AbstractCheck import AbstractCheck


class IconSizesCheck(AbstractCheck):
    file_size_regex = re.compile(r'/icons/[^/]+/(?P<x>\d+)x(?P<y>\d+)/')
    info_size_regex = re.compile(r'(?P<x>\d+) x (?P<y>\d+)')

    def check(self, pkg):
        if pkg.is_source:
            return

        for fname, pkgfile in pkg.files.items():
            if '/animations/' in fname:
                continue

            res = self.file_size_regex.search(fname)
            res2 = self.info_size_regex.search(pkgfile.magic)
            if res and res2:
                sizes = (res.group('x'), res.group('y'))
                actualsizes = (res2.group('x'), res2.group('y'))
                if abs(int(sizes[0]) - int(actualsizes[0])) > 2 or \
                        abs(int(sizes[1]) - int(actualsizes[1])) > 2:
                    self.output.add_info('E', pkg, 'wrong-icon-size', fname,
                                         'expected:', 'x'.join(sizes), 'actual:', 'x'.join(actualsizes))
