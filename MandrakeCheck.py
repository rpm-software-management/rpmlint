#############################################################################
# File		: MandrakeCheck.py
# Package	: rpmlint
# Author	: Frederic Lepied
# Created on	: Tue Sep 28 00:05:33 1999
# Version	: $Id$
# Purpose	: check the Mandrake specificities in a binary rpm package.
#############################################################################

import AbstractCheck
import rpm
import re

class MandrakeCheck(AbstractCheck.AbstractCheck):

    man_regex=re.compile("/man./")
    info_regex=re.compile("/info/")
    bz2_regex=re.compile(".bz2$")
    
    def __init__(self):
	AbstractCheck.AbstractCheck.__init__(self, "MandrakeCheck")

    def check(self, pkg, verbose):
	# Check only binary package
	if pkg.isSource():
	    return
	
	if pkg[rpm.RPMTAG_VENDOR] != "MandrakeSoft":
	    print "W:", pkg.name, "not-mandrakesoft-vendor", pkg[rpm.RPMTAG_VENDOR]

	if pkg[rpm.RPMTAG_DISTRIBUTION] != "Mandrake":
	    print "W:", pkg.name, "not-mandrake-distribution", pkg[rpm.RPMTAG_DISTRIBUTION]

	# Check the listing of files
	list=pkg[rpm.RPMTAG_FILENAMES]
	
	if list:
	    for f in list:
		if MandrakeCheck.man_regex.search(f) and not MandrakeCheck.bz2_regex.search(f):
		    print "W:", pkg.name, "manpage-not-bzipped", f
		if MandrakeCheck.info_regex.search(f) and not MandrakeCheck.bz2_regex.search(f):
		    print "W:", pkg.name, "infopage-not-bzipped", f

# Create an object to enable the auto registration of the test
check=MandrakeCheck()

# MandrakeCheck.py ends here
