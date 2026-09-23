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

    Files sharing one md5 hash are further grouped by (rdev, inode) so
    hardlinked files can be told apart from genuine duplicates.
    """

    DUPLICATES_DISPLAY_LIMIT = 5

    def __init__(self, config, output):
        super().__init__(config, output)
        self.min_size = self.config.configuration.get('DuplicatesMinSize', 0)

    def check(self, pkg):
        if pkg.is_source:
            return

        md5s = {}
        sizes = {}
        total_dup_size = 0

        for fname, pkgfile in pkg.files.items():
            if fname in pkg.ghost_files or not stat.S_ISREG(pkgfile.mode):
                continue

            # Skip small files
            if pkgfile.size <= self.min_size:
                continue

            # fillup md5s and sizes dicts
            md5s.setdefault(pkgfile.md5, set()).add(pkgfile)
            sizes[pkgfile.md5] = pkgfile.size

        # process duplicates
        for md5_hash in md5s:
            # obtain the list of the files with the same md5 hash
            duplicates = md5s[md5_hash]

            # continue, there is no duplicate
            if len(duplicates) == 1:
                continue

            duplicates = sorted(duplicates, key=lambda x: x.name)
            first = duplicates.pop()

            # group the files by (rdev, inode); each group is either a set
            # of hardlinked files or a single genuine duplicate
            inode_groups = {}
            for duplicate in [first] + duplicates:
                key = (duplicate.rdev, duplicate.inode)
                inode_groups.setdefault(key, []).append(duplicate)

            # report hardlinked files spanning different prefixes (and
            # hardlinked config files) inside every inode group, even in
            # groups that also contain genuine duplicates
            for group in inode_groups.values():
                if len(group) == 1:
                    continue
                group = sorted(group, key=lambda x: x.name)
                group_first = group.pop()
                group_first_is_config = group_first.name in pkg.config_files
                group_prefix = self._get_prefix(group_first)
                for duplicate in group:
                    if group_prefix != self._get_prefix(duplicate):
                        self.output.add_info('E', pkg,
                                             'hardlink-across-partition',
                                             group_first.name, duplicate.name)
                    if group_first_is_config and duplicate.name in pkg.config_files:
                        self.output.add_info('E', pkg,
                                             'hardlink-across-config-files',
                                             group_first.name, duplicate.name)

            # more than one inode group means there is at least one genuine
            # duplicate (same content, different inode); always report it,
            # no matter which prefixes the files live in
            if len(inode_groups) > 1 and sizes[md5_hash]:
                display_duplicates = duplicates[:self.DUPLICATES_DISPLAY_LIMIT]
                other_duplicates = len(duplicates[self.DUPLICATES_DISPLAY_LIMIT:])

                description = ':'.join([x.name for x in display_duplicates])
                if other_duplicates > 0:
                    description += f':(and {other_duplicates} more)'
                self.output.add_info('W', pkg, 'files-duplicate', first.name,
                                     description)

            # every inode group beyond the first one is a wasted copy
            total_dup_size += sizes[md5_hash] * (len(inode_groups) - 1)

        # check the overall size of the duplicates and print an error if it's
        # too much
        if total_dup_size > 100000:
            self.output.add_info('E', pkg, 'files-duplicated-waste',
                                 total_dup_size)

    @staticmethod
    def _get_prefix(pkgfile):
        """Return first two directories in the given path."""
        pathlist = pkgfile.name.split('/')
        if len(pathlist) == 3:
            return '/'.join(pathlist[0:2])
        return '/'.join(pathlist[0:3])
