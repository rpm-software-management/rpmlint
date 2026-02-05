from rpmlint.checks.AbstractCheck import AbstractCheck


class AtomicUpdateCheck(AbstractCheck):

    """
    Requirements for atomic updates:
        * All files must be stored inside the snapshot, which is in our case /etc and /usr, not /var,
          /opt, /srv, /usr/local or anything else.
        * (Re)starting daemons is not possible.
        * Modifying files outside of /usr and /etc is not possible.
        * Modifications outside the snapshot have to be done via systemd-tmpfiles and systemd services.
    This check currently only implements checking for files at illegal paths.
    """

    def __init__(self, config, output):
        super().__init__(config, output)
        self.check_ghosts = self.config.configuration['AtomicCheckGhosts']
        self.allowed_dirs = self.config.configuration['AtomicAllowedDirs']
        self.disallowed_subdirs = self.config.configuration['AtomicDisallowedSubdirs']

    def check(self, pkg):
        if pkg.is_source:
            return

        # Check for files stored outside the snapshot
        self._check_paths(pkg, self.check_ghosts)

    def _check_paths(self, pkg, check_ghosts=False):
        for file in pkg.files.keys():
            if file in pkg.ghost_files:
                continue  # Ghosts are only handled if explicitly desired
            if not (self._check_single_path(file)):
                self.output.add_info('E', pkg, 'dir-or-file-outside-snapshot', file)
        if check_ghosts:
            for ghost in pkg.ghost_files:
                if not (self._check_single_path(ghost)):
                    self.output.add_info('W', pkg, 'ghost-outside-snapshot', ghost)

    def _check_single_path(self, file):
        return (
            file.startswith(tuple(self.allowed_dirs)) and
            not file.startswith(tuple(self.disallowed_subdirs))
        )
