#############################################################################
# Project         : Linux-Mandrake
# Module          : rpmlint
# File            : PostCheck.py
# Version         : $Id$
# Author          : Frederic Lepied
# Created On      : Wed Jul  5 13:30:17 2000
# Purpose         : Check post/pre scripts
#############################################################################

from Filter import *
import AbstractCheck
import rpm
import re

class PostCheck(AbstractCheck.AbstractCheck):
    braces_regex=re.compile("[^#]*%{")
    
    def __init__(self):
        AbstractCheck.AbstractCheck.__init__(self, "PostCheck")

    def check(self, pkg, verbose):
	# Check only binary package
	if pkg.isSource():
	    return

        for tag in ((rpm.RPMTAG_PREIN, "%pre"), (rpm.RPMTAG_POSTIN, "%post"),
                    (rpm.RPMTAG_PREUN, "%preun"), (rpm.RPMTAG_POSTUN, "%postun")):
            script = pkg[tag[0]]
            if script and PostCheck.braces_regex.search(script):
                printError(pkg, "braces-in-" + tag[1])

# Create an object to enable the auto registration of the test
check=PostCheck()

# PostCheck.py ends here
