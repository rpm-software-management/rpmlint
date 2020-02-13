from rpmlint.checks.AbstractCheck import AbstractCheck


class ConfigFilesCheck(AbstractCheck):
    """
    Check that configuration files are in a proper location and marked as
    'noreplace'.
    """
    def check_binary(self, pkg):
        for filename in pkg.config_files:
            self._check_non_confdir_files(pkg, filename)
            self._check_noreplace_files(pkg, filename)

    def _check_non_confdir_files(self, pkg, fn):
        """
        Check if the configuration file is in /etc or /var directory.

        Print a warning if it's not.
        """
        if not fn.startswith('/etc/') and not fn.startswith('/var/'):
            self.output.add_info('W', pkg,
                                 'non-etc-or-var-file-marked-as-conffile', fn)

    def _check_noreplace_files(self, pkg, fn):
        """
        Check if the configuration file has 'noreplace' flag.

        Print a warning if there is no 'noreplace' tag.
        """
        if fn not in pkg.noreplace_files:
            self.output.add_info('W', pkg,
                                 'conffile-without-noreplace-flag', fn)
