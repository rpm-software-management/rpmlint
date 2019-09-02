import os
import stat

from rpmlint.checks.AbstractCheck import AbstractCheck


class DuplicatesCheck(AbstractCheck):
    @staticmethod
    def get_prefix(filename):
        pathlist = str.split(filename, '/')
        if len(pathlist) == 3:
            return '/'.join(pathlist[0:2])
        return '/'.join(pathlist[0:3])

    def check(self, pkg):
        if pkg.isSource():
            return

        md5s = {}
        sizes = {}
        files = pkg.files()
        configFiles = pkg.configFiles()

        for f, pkgfile in files.items():
            if f in pkg.ghostFiles():
                continue

            if not stat.S_ISREG(pkgfile.mode):
                continue

            md5s.setdefault(pkgfile.md5, set()).add(f)
            sizes[pkgfile.md5] = pkgfile.size

        total = 0
        for f in md5s:
            duplicates = md5s[f]
            if len(duplicates) == 1:
                continue

            duplicates = sorted(list(duplicates))
            first = duplicates.pop()
            first_is_config = False
            if first in configFiles:
                first_is_config = True

            partition = self.get_prefix(first)

            st = os.stat(pkg.dirName() + '/' + first)
            diff = 1 + len(duplicates) - st[stat.ST_NLINK]
            if diff <= 0:
                for duplicate in duplicates:
                    if partition != self.get_prefix(duplicate):
                        self.output.add_info('E', pkg, 'hardlink-across-partition', first, duplicate)
                    if first_is_config and duplicate in configFiles:
                        self.output.add_info('E', pkg, 'hardlink-across-config-files', first, duplicate)
                continue

            for duplicate in duplicates:
                if partition != self.get_prefix(duplicate):
                    diff = diff - 1
            total += sizes[f] * diff
            if sizes[f] and diff > 0:
                self.output.add_info('W', pkg, 'files-duplicate', first, ':'.join(duplicates))

        if total > 100000:
            self.output.add_info('E', pkg, 'files-duplicated-waste', total)
