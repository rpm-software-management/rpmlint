#############################################################################
# File		: SourceCheck.py
# Package	: rpmlint
# Author	: Frederic Lepied
# Created on	: Wed Oct 27 21:17:03 1999
# Version	: $Id$
# Purpose	: verify source package correctness.
#############################################################################

from Filter import *
import AbstractCheck
import re
import Config

spec_regex=re.compile('.spec$')
bz2_regex=re.compile('.bz2$')
gz_regex=re.compile('gz$')
source_regex=re.compile('\\.(tar|patch|tgz|diff)$')
use_bzip2=Config.getOption('UseBzip2', 1)

class SourceCheck(AbstractCheck.AbstractCheck):

    
    def __init__(self):
	AbstractCheck.AbstractCheck.__init__(self, 'SourceCheck')

    def check(self, pkg, verbose):
	# Check only source package
	if not pkg.isSource():
	    return

	# process file list
	files=pkg.files()
	spec_file=None
	for f in files.keys():
	    if spec_regex.search(f):
		if spec_file:
		    printError(pkg, 'multiple-specfiles', spec_file, f)
		else:
		    spec_file=f
	    elif source_regex.search(f):
		if use_bzip2:
		    if not bz2_regex.search(f):
			printWarning(pkg, 'source-or-patch-not-bzipped', f)
		else:
		    if not gz_regex.search(f):
			printWarning(pkg, 'source-or-patch-not-gzipped', f)
	    perm=files[f][0] & 07777
	    if perm != 0644:
		printWarning(pkg, 'strange-permission', f, oct(perm))	    
		
check=SourceCheck()

# SourceCheck.py ends here
