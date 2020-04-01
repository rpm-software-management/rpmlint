from rpmlint.checks.AbstractCheck import AbstractCheck


class MixedOwnershipCheck(AbstractCheck):
    def check(self, pkg):
        """
        Check for mixed permissions in the directory path.

        If folder is owned by i.e. nobody then the files there shouldn't
        be owned by other user either, as then nobody could replace the files
        and inject anything.
        """
        if pkg.is_source:
            return

        for path, info in pkg.files.items():
            parent = path.rpartition('/')[0]

            # In case parent folder is not part of this RPM we can't verify it
            if parent not in pkg.files:
                continue
            parent_owner = pkg.files[parent].user
            # root user is trusted
            if parent_owner in ('root', '0'):
                continue
            if info.user != parent_owner:
                message = f'Path "{path}" owned by "{info.user}" is stored in directory owned by "{parent_owner}"'
                self.output.add_info('E', pkg, 'file-parent-ownership-mismatch', message)
