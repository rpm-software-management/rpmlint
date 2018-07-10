# -*- coding: utf-8 -*-
#############################################################################
# Project         : Mandriva Linux
# Module          : rpmlint
# File            : LSBCheck.py
# Author          : Frederic Lepied
# Created On      : Tue Jan 30 14:44:37 2001
# Purpose         : LSB non compliance checks
#############################################################################

import re

import rpm

import AbstractCheck
from Filter import addDetails, printError


version_regex = re.compile('^[a-zA-Z0-9.+]+$')
name_regex = re.compile('^[a-z0-9.+-]+$')


class LSBCheck(AbstractCheck.AbstractCheck):

    def __init__(self):
        AbstractCheck.AbstractCheck.__init__(self, "LSBCheck")

    def check(self, pkg):

        name = pkg.name
        if name and not name_regex.search(name):
            printError(pkg, 'non-lsb-compliant-package-name', name)

        version = pkg[rpm.RPMTAG_VERSION]
        if version and not version_regex.search(version):
                printError(pkg, 'non-lsb-compliant-version', version)

        release = pkg[rpm.RPMTAG_RELEASE]
        if release and not version_regex.search(release):
                printError(pkg, 'non-lsb-compliant-release', release)


# Create an object to enable the auto registration of the test
check = LSBCheck()

addDetails(
'non-lsb-compliant-package-name',
"""Your package name contains an illegal character. Use only
alphanumeric symbols in your package name.""",

'non-lsb-compliant-version',
"""Your version number contains an illegal character. Use only
lowercase letters and/or numbers.""",

'non-lsb-compliant-release',
"""Your version number contains an illegal character. Use only
lowercase letters and/or numbers.""",

)

# LSBCheck.py ends here
