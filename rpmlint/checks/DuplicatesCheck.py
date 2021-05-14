import stat

from rpmlint.checks.AbstractCheck import AbstractCheck


class DuplicatesCheck(AbstractCheck):
    """
    Search for the duplicated files in the package.

    It uses the following structures:

    md5s
    - key: md5 hash of the file
    - values: files with this hash

    sizes
    - key: md5 hash of the file
    - values: size of the file
    """

    def check(self, pkg):
        if pkg.is_source:
            return

        md5s = {}
        sizes = {}
        hardlinks = {}
        total_dup_size = 0

        for fname, pkgfile in pkg.files.items():
            if fname in pkg.ghost_files or not stat.S_ISREG(pkgfile.mode):
                continue

            # fillup md5s and sizes dicts
            md5s.setdefault(pkgfile.md5, set()).add(pkgfile)
            sizes[pkgfile.md5] = pkgfile.size
            key = (pkgfile.rdev, pkgfile.inode)
            if key not in hardlinks:
                hardlinks[key] = 0
            hardlinks[key] += 1

        # process duplicates
        for md5_hash in md5s:
            # obtain the list of the files with the same md5 hash
            duplicates = md5s[md5_hash]

            # continue, there is no duplicate
            if len(duplicates) == 1:
                continue

            duplicates = sorted(duplicates, key=lambda x: x.name)
            first = duplicates.pop()
            first_is_config = False
            if first.name in pkg.config_files:
                first_is_config = True

            prefix = self._get_prefix(first)

            # 1 (first) + number of others - number of hard links
            # (keeps track of how many directories have entries for this file)
            # diff is a number of files that are duplicates but not hard-links
            key = (first.rdev, first.inode)
            diff = 1 + len(duplicates) - hardlinks[key]

            if diff <= 0:
                # now we have just hard-links in duplicates
                for duplicate in duplicates:
                    if prefix != self._get_prefix(duplicate):
                        self.output.add_info('E', pkg,
                                             'hardlink-across-partition',
                                             first.name, duplicate.name)
                    if first_is_config and duplicate.name in pkg.config_files:
                        self.output.add_info('E', pkg,
                                             'hardlink-across-config-files',
                                             first.name, duplicate.name)
                continue

            # now we know that there are some duplicates that are not links
            for duplicate in duplicates:
                if prefix != self._get_prefix(duplicate):
                    # if the duplicate is in a different prefix, we can ignore
                    # it since it can't be linked anyway
                    diff = diff - 1

            # if there is still a positive diff (i.e. there is a duplicate that
            # is not a link and wasn't ignored by the previous step),
            # report a warning
            if sizes[md5_hash] and diff > 0:
                self.output.add_info('W', pkg, 'files-duplicate', first.name,
                                     ':'.join([x.name for x in duplicates]))
            total_dup_size += sizes[md5_hash] * diff

        # check the overall size of the duplicates and print an error if it's
        # too much
        if total_dup_size > 100000:
            self.output.add_info('E', pkg, 'files-duplicated-waste',
                                 total_dup_size)

    @staticmethod
    def _get_prefix(pkgfile):
        """Return first two directories in the given path."""
        pathlist = str.split(pkgfile.name, '/')
        if len(pathlist) == 3:
            return '/'.join(pathlist[0:2])
        return '/'.join(pathlist[0:3])
