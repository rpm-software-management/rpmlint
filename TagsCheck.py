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

VALID_GROUPS=(
    "Amusements/Games",
    "Amusements/Graphics",
    "Applications/Archiving",
    "Applications/Communications",
    "Applications/Databases",
    "Applications/Editors",
    "Applications/Emulators",
    "Applications/Engineering",
    "Applications/File",
    "Applications/Internet",
    "Applications/Multimedia",
    "Applications/Productivity",
    "Applications/Publishing",
    "Applications/System",
    "Applications/Text",
    "Development/Debuggers",
    "Development/Languages",
    "Development/Libraries",
    "Development/System",
    "Development/Tools",
    "Documentation",
    "System Environment/Base",
    "System Environment/Daemons",
    "System Environment/Kernel",
    "System Environment/Libraries",
    "System Environment/Shells",
    "User Interface/Desktops",
    "User Interface/X",
    "User Interface/X Hardware Support"
    )

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

	if pkg[rpm.RPMTAG_SOURCE]:
	    print "I:", pkg.name, "source-tag", pkg[rpm.RPMTAG_SOURCE]

	if not pkg[rpm.RPMTAG_DESCRIPTION]:
	    print "E:", pkg.name, "no-description-tag"
	    
	group=pkg[rpm.RPMTAG_GROUP]
	if not pkg[rpm.RPMTAG_GROUP]:
	    print "E:", pkg.name, "no-group-tag"
	else:
	    if not group in VALID_GROUPS:
		print "W: non-standard-group", group
	
	if not pkg[rpm.RPMTAG_CHANGELOGTEXT]:
	    print "E:", pkg.name, "no-changelogtext-tag"

check=TagsCheck()

# TagsCheck.py ends here
