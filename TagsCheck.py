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
import Config

DEFAULT_VALID_GROUPS=(
    "System/Servers",
    "System/Kernel and hardware",
    "System/Libraries",
    "System/XFree86",
    "System/Fonts/Console",
    "System/Fonts/True type",
    "System/Fonts/Type1",
    "System/Fonts/X11 bitmap",
    "System/Base",
    "System/Configuration/Hardware",
    "System/Configuration/Packaging",
    "System/Configuration/Networking",
    "System/Configuration/Printing",
    "System/Configuration/Boot and Init",
    "System/Configuration/Other",
    "System/Internationalization",
    "Development/Kernel",
    "Development/Databases",
    "Development/Perl",
    "Development/Python",
    "Development/C",
    "Development/C++",
    "Development/Java",
    "Development/GNOME and GTK+",
    "Development/KDE and QT",
    "Development/Other",
    "Sciences/Astronomy",
    "Sciences/Biology",
    "Sciences/Chemistry",
    "Sciences/Computer science",
    "Sciences/Geosciences",
    "Sciences/Mathematics",
    "Sciences/Physics",
    "Sciences/Other",
    "Communications",
    "Databases",
    "Editors",
    "Emulators",
    "Games/Adventure",
    "Games/Arcade",
    "Games/Boards",
    "Games/Cards",
    "Games/Puzzles",
    "Games/Sports",
    "Games/Strategy",
    "Games/Other",
    "Toys",
    "Archiving/Compression",
    "Archiving/Cd burning",
    "Archiving/Backup",
    "Archiving/Other",
    "Monitoring",
    "Sound",
    "Graphics",
    "Video",
    "Networking/File transfer",
    "Networking/IRC",
    "Networking/ICQ",
    "Networking/Chat",
    "Networking/News",
    "Networking/Mail",
    "Networking/WWW",
    "Networking/Remote access",
    "Networking/Other",
    "Office",
    "Publishing",
    "Terminals",
    "Shells",
    "File tools",
    "Text tools",
    "Graphical desktop/GNOME",
    "Graphical desktop/Icewm",
    "Graphical desktop/FVWM based",
    "Graphical desktop/KDE",
    "Graphical desktop/Sawmill",
    "Graphical desktop/Window Maker",
    "Graphical desktop/Enlightenment",
    "Graphical desktop/Other",
    "Books/Howtos",
    "Books/Faqs",
    "Books/Computer books",
    "Books/Litterature",
    "Books/Other"
    )

class TagsCheck(AbstractCheck.AbstractCheck):
    basename_regex=re.compile("/?([^/]+)$")
    changelog_version_regex=re.compile("[^>]([^ >]+)$")
    valid_groups=Config.getOption("ValidGroups", DEFAULT_VALID_GROUPS)
    release_ext=Config.getOption("ReleaseExtension", "mdk")
    extension_regex=release_ext and re.compile(release_ext + "$")
    use_version_in_changelog=Config.getOption("UseVersionInChangelog", 1)
    
    def __init__(self):
	AbstractCheck.AbstractCheck.__init__(self, "TagsCheck")

    def check(self, pkg, verbose):

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

	version=pkg[rpm.RPMTAG_VERSION]
	if not version:
	    printError(pkg, "no-version-tag")

        release=pkg[rpm.RPMTAG_RELEASE]
	if not release:
	    printError(pkg, "no-release-tag")
        elif TagsCheck.release_ext and not TagsCheck.extension_regex.search(release):
            printWarning(pkg, "not-standard-release-extension", release)

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
	    if not group in TagsCheck.valid_groups:
		printWarning(pkg, "non-standard-group", group)

	changelog=pkg[rpm.RPMTAG_CHANGELOGNAME]
        if not changelog:
	    printError(pkg, "no-changelogname-tag")
        elif TagsCheck.use_version_in_changelog:
            ret=TagsCheck.changelog_version_regex.search(changelog[0])
            if not ret:
                printWarning(pkg, "no-version-in-last-changelog")
            elif version and release:
                if version + "-" + release != ret.group(1):
                    printWarning(pkg, "incoherent-version-in-changelog", ret.group(1), version + "-" + release)
                                 
check=TagsCheck()

# TagsCheck.py ends here
