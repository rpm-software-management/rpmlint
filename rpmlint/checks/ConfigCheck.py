#############################################################################
# File          : ConfigCheck.py
# Package       : rpmlint
# Author        : Frederic Lepied
# Created on    : Sun Oct  3 21:48:20 1999
# Purpose       :
#############################################################################

from rpmlint.checks.AbstractCheck import AbstractCheck


class ConfigCheck(AbstractCheck):
    def __init__(self, config, output):
        super().__init__(config, output)
        self.output.error_details.update(config_details_dict)

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


# Add information about checks
config_details_dict = {
'score-file-must-not-be-conffile':
"""A file in /var/lib/games/ is a configuration file. Store your conf
files in /etc instead.""",

'non-etc-or-var-file-marked-as-conffile':
"""A file not in /etc or /var is marked as being a configuration file.
Please put your conf files in /etc or /var.""",

'conffile-without-noreplace-flag':
"""A configuration file is stored in your package without the noreplace flag.
A way to resolve this is to put the following in your SPEC file:

%config(noreplace) /etc/your_config_file_here
""",
}
