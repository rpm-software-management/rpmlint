#############################################################################
# File		: TagsCheck.py
# Package	: rpmlint
# Author	: Frederic Lepied
# Created on	: Tue Sep 28 00:03:24 1999
# Version	: $Id$
# Purpose	: Check a package to see if some rpm tags are present
#############################################################################

from Filter import *
import AbstractCheck
import rpm
import string
import re

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
    basename_regex=re.compile("/?([^/]+)$")
    
    def __init__(self):
	AbstractCheck.AbstractCheck.__init__(self, "TagsCheck")

    def check(self, pkg, verbose):
	# Check only binary package
	if not pkg[rpm.RPMTAG_PACKAGER]:
	    printError(pkg, "no-packager-tag")

	name=pkg[rpm.RPMTAG_NAME]
	if not name:
	    printError(pkg, "no-name-tag")
	elif name:
	    res=TagsCheck.basename_regex.search(pkg.filename)
	    if res:
		basename=res.group(1)
		if name != basename[0:len(name)]:
		    printWarning(pkg, "non-coherent-filename", name, basename)
	
	if not pkg[rpm.RPMTAG_VERSION]:
	    printError(pkg, "no-version-tag")

	if not pkg[rpm.RPMTAG_RELEASE]:
	    printError(pkg, "no-release-tag")

	summary=pkg[rpm.RPMTAG_SUMMARY]
	if not summary:
	    printError(pkg, "no-summary-tag")
	elif string.find(summary, "\n") != -1:
	    printError(pkg, "summary-on-multiple-lines")
	    print summary
	    
	if not pkg[rpm.RPMTAG_DESCRIPTION]:
	    printError(pkg, "no-description-tag")
	    
	group=pkg[rpm.RPMTAG_GROUP]
	if not pkg[rpm.RPMTAG_GROUP]:
	    printError(pkg, "no-group-tag")
	else:
	    if not group in VALID_GROUPS:
		printWarning(pkg, "non-standard-group", group)
	
	if not pkg[rpm.RPMTAG_CHANGELOGTEXT]:
	    printError(pkg, "no-changelogtext-tag")

check=TagsCheck()

# TagsCheck.py ends here
