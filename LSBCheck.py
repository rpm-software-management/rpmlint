#---------------------------------------------------------------
# Project         : Linux-Mandrake
# Module          : rpmlint
# File            : LSBCheck.py
# Version         : $Id$
# Author          : Frederic Lepied
# Created On      : Tue Jan 30 14:44:37 2001
# Purpose         : LSB non compliance checks
#---------------------------------------------------------------

from Filter import *
import AbstractCheck
import rpm
import re

version_regex=re.compile('^[a-zA-Z0-9.+]+$')
name_regex=re.compile('^[a-z0-9.+-]+$')

class LSBCheck(AbstractCheck.AbstractCheck):
    
    def __init__(self):
	AbstractCheck.AbstractCheck.__init__(self, "LSBCheck")

    def check(self, pkg, verbose):
	# Check only binary package
	if pkg.isSource():
	    return

	name=pkg[rpm.RPMTAG_NAME]
	if name and not name_regex.search(name):
	    printError(pkg, 'non-lsb-compliant-package-name', name)

	version=pkg[rpm.RPMTAG_VERSION]
	if version and not version_regex.search(version):
	    printError(pkg, 'non-lsb-compliant-version', version)

        release=pkg[rpm.RPMTAG_RELEASE]
	if release and not version_regex.search(release):
	    printError(pkg, 'non-lsb-compliant-release', release)

# Create an object to enable the auto registration of the test
check=LSBCheck()

# LSBCheck.py ends here
