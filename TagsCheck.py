#############################################################################
# File		: TagsCheck.py
# Package	: rpmlint
# Author	: Frederic Lepied
# Created on	: Tue Sep 28 00:03:24 1999
# Version	: $Id$
# Purpose	: Check a binary package to see if some rpm tags are present
#############################################################################

import AbstractCheck
import rpm

class TagsCheck(AbstractCheck.AbstractCheck):
    def __init__(self):
	AbstractCheck.AbstractCheck.__init__(self, "TagsCheck")

    def check(self, pkg, verbose):
	# Check only binary package
	if pkg.isSource():
	    return
	
	if not pkg[rpm.RPMTAG_PACKAGER]:
	    print "E:", pkg.name, "no-packager-tag"
	if not pkg[rpm.RPMTAG_NAME]:
	    print "E:", pkg.name, "no-name-tag"
	if not pkg[rpm.RPMTAG_VERSION]:
	    print "E:", pkg.name, "no-version-tag"
	if not pkg[rpm.RPMTAG_RELEASE]:
	    print "E:", pkg.name, "no-release-tag"
	if not pkg[rpm.RPMTAG_SUMMARY]:
	    print "E:", pkg.name, "no-summary-tag"
	if not pkg[rpm.RPMTAG_DESCRIPTION]:
	    print "E:", pkg.name, "no-description-tag"
	if not pkg[rpm.RPMTAG_GROUP]:
	    print "E:", pkg.name, "no-group-tag"
	if not pkg[rpm.RPMTAG_CHANGELOGTEXT]:
	    print "E:", pkg.name, "no-changelogtext-tag"

check=TagsCheck()

# TagsCheck.py ends here
