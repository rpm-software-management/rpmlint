#############################################################################
# File		: DistributionCheck.py
# Package	: rpmlint
# Author	: Frederic Lepied
# Created on	: Tue Sep 28 00:05:33 1999
# Version	: $Id$
# Purpose	: check the Distribution specificities in a binary rpm package.
#############################################################################

from Filter import *
import AbstractCheck
import rpm
import re
import Config

class DistributionCheck(AbstractCheck.AbstractCheck):

    man_regex=re.compile("/man./")
    info_regex=re.compile("/info/")
    info_dir_regex=re.compile("/info/dir$")
    bz2_regex=re.compile(".bz2$")
    gz_regex=re.compile(".gz$")
    vendor=Config.getOption("Vendor", "MandrakeSoft")
    distribution=Config.getOption("Distribution", "Mandrake Linux")
    use_bzip2=Config.getOption("UseBzip2", 1)
    
    def __init__(self):
	AbstractCheck.AbstractCheck.__init__(self, "DistributionCheck")

    def check(self, pkg, verbose):
	# Check only binary package
	if pkg.isSource():
	    return
	
	if pkg[rpm.RPMTAG_VENDOR] != DistributionCheck.vendor:
	    printWarning(pkg, "invalid-vendor", pkg[rpm.RPMTAG_VENDOR])

	if pkg[rpm.RPMTAG_DISTRIBUTION] != DistributionCheck.distribution:
	    printWarning(pkg, "invalid-distribution", pkg[rpm.RPMTAG_DISTRIBUTION])

	# Check the listing of files
	list=pkg[rpm.RPMTAG_FILENAMES]
	
	if list:
	    for f in list:
		if DistributionCheck.man_regex.search(f):
		    if DistributionCheck.use_bzip2:
			if not DistributionCheck.bz2_regex.search(f):
			    printWarning(pkg, "manpage-not-bzipped", f)
		    elif not DistributionCheck.gz_regex.search(f):
			printWarning(pkg, "manpage-not-gzipped", f)
		if DistributionCheck.info_regex.search(f) and not DistributionCheck.info_dir_regex.search(f):
		    if DistributionCheck.use_bzip2:
			if not DistributionCheck.bz2_regex.search(f):
			    printWarning(pkg, "infopage-not-bzipped", f)
		    elif not DistributionCheck.gz_regex.search(f):
			    printWarning(pkg, "infopage-not-gzipped", f)

# Create an object to enable the auto registration of the test
check=DistributionCheck()

if Config.info:
    addDetails(
'invalid-vendor',
"""
""",

'invalid-distribution',
"""
""",

'manpage-not-bzipped',
"""
""",

'manpage-not-gzipped',
"""
""",

'infopage-not-bzipped',
"""
""",

'infopage-not-gzipped',
"""
""",

)
# DistributionCheck.py ends here
