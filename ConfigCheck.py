# -*- coding: utf-8 -*-
#############################################################################
# File          : ConfigCheck.py
# Package       : rpmlint
# Author        : Frederic Lepied
# Created on    : Sun Oct  3 21:48:20 1999
# Purpose       :
#############################################################################

import AbstractCheck
from Filter import addDetails, printError, printWarning


class ConfigCheck(AbstractCheck.AbstractCheck):

    def __init__(self):
        AbstractCheck.AbstractCheck.__init__(self, "ConfigCheck")

    def check_binary(self, pkg):
        config_files = pkg.configFiles()
        noreplace_files = pkg.noreplaceFiles()

        for c in config_files:
            if c.startswith("/var/lib/games/"):
                printError(pkg, "score-file-must-not-be-conffile", c)
            elif not c.startswith("/etc/") and not c.startswith("/var/"):
                printWarning(pkg, "non-etc-or-var-file-marked-as-conffile", c)

            if c not in noreplace_files:
                printWarning(pkg, "conffile-without-noreplace-flag", c)

# Create an object to enable the auto registration of the test
check = ConfigCheck()

# Add information about checks
addDetails(
'score-file-must-not-be-conffile',
"""A file in /var/lib/games/ is a configuration file. Store your conf
files in /etc instead.""",

'non-etc-or-var-file-marked-as-conffile',
"""A file not in /etc or /var is marked as being a configuration file.
Please put your conf files in /etc or /var.""",

'conffile-without-noreplace-flag',
"""A configuration file is stored in your package without the noreplace flag.
A way to resolve this is to put the following in your SPEC file:

%config(noreplace) /etc/your_config_file_here
""",

)

# ConfigCheck.py ends here

# ex: ts=4 sw=4 et
