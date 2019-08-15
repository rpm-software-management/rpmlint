#############################################################################
# File          : ConfigCheck.py
# Package       : rpmlint
# Author        : Frederic Lepied
# Created on    : Sun Oct  3 21:48:20 1999
# Purpose       :
#############################################################################

from rpmlint.checks.AbstractCheck import AbstractCheck


class ConfigCheck(AbstractCheck):
    def check_binary(self, pkg):
        config_files = pkg.configFiles()
        noreplace_files = pkg.noreplaceFiles()

        for c in config_files:
            if c.startswith('/var/lib/games/'):
                self.output.add_info('E', pkg, 'score-file-must-not-be-conffile', c)
            elif not c.startswith('/etc/') and not c.startswith('/var/'):
                self.output.add_info('W', pkg, 'non-etc-or-var-file-marked-as-conffile', c)
            if c not in noreplace_files:
                self.output.add_info('W', pkg, 'conffile-without-noreplace-flag', c)
