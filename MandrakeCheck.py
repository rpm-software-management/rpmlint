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
import Config

class MandrakeCheck(AbstractCheck.AbstractCheck):

    man_regex=re.compile("/man./")
    info_regex=re.compile("/info/")
    bz2_regex=re.compile(".bz2$")
    gz_regex=re.compile(".gz$")
    vendor=Config.getOption("Vendor", "MandrakeSoft")
    distribution=Config.getOption("Distribution", "Mandrake")
    use_bzip2=Config.getOption("UseBzip2", 1)
    
    def __init__(self):
	AbstractCheck.AbstractCheck.__init__(self, "MandrakeCheck")

    def check(self, pkg, verbose):
	# Check only binary package
	if pkg.isSource():
	    return
	
	if pkg[rpm.RPMTAG_VENDOR] != MandrakeCheck.vendor:
	    print "W:", pkg.name, "invalid-vendor", pkg[rpm.RPMTAG_VENDOR]

	if pkg[rpm.RPMTAG_DISTRIBUTION] != MandrakeCheck.distribution:
	    print "W:", pkg.name, "invalid-distribution", pkg[rpm.RPMTAG_DISTRIBUTION]

	# Check the listing of files
	list=pkg[rpm.RPMTAG_FILENAMES]
	
	if list:
	    for f in list:
		if MandrakeCheck.man_regex.search(f):
		    if MandrakeCheck.use_bzip2:
			if not MandrakeCheck.bz2_regex.search(f):
			    print "W:", pkg.name, "manpage-not-bzipped", f
		    elif not MandrakeCheck.gz_regex.search(f):
			print "W:", pkg.name, "manpage-not-gzipped", f
		if MandrakeCheck.info_regex.search(f):
		    if MandrakeCheck.use_bzip2:
			if not MandrakeCheck.bz2_regex.search(f):
			    print "W:", pkg.name, "infopage-not-bzipped", f
		    elif not MandrakeCheck.gz_regex.search(f):
			    print "W:", pkg.name, "infopage-not-gzipped", f

# Create an object to enable the auto registration of the test
check=MandrakeCheck()

# MandrakeCheck.py ends here
