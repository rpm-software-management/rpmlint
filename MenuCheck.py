#---------------------------------------------------------------
# Project         : Mandrake
# Module          : rpmlint
# File            : MenuCheck.py
# Version         : $Id$
# Author          : Frederic Lepied
# Created On      : Mon Mar 20 07:43:37 2000
#---------------------------------------------------------------

from Filter import *
import AbstractCheck
import rpm
import re
import commands
import string
import sys
import stat
import Pkg

DEFAULT_VALID_SECTIONS=(
    "Configuration/Hardware",
    "Configuration/Packaging",
    "Configuration/Networking",
    "Configuration/Printing",
    "Configuration/Boot and Init",
    "Configuration/Other",
    "Applications/Development/Interpreters",
    "Applications/Development/Code generators",
    "Applications/Development/Development environments",
    "Applications/Development/Tools",
    "Applications/Sciences/Astronomy",
    "Applications/Sciences/Biology",
    "Applications/Sciences/Chemistry",
    "Applications/Sciences/Computer science",
    "Applications/Sciences/Geosciences",
    "Applications/Sciences/Mathematics",
    "Applications/Sciences/Physics",
    "Applications/Sciences/Other",
    "Applications/Communications",
    "Applications/Editors",
    "Applications/Emulators",
    "Applications/Archiving/Compression",
    "Applications/Archiving/Cd burning",
    "Applications/Archiving/Backup",
    "Applications/Archiving/Other",
    "Applications/Monitoring",
    "Applications/Publishing",
    "Terminals",
    "Applications/Shells",
    "Applications/File tools",
    "Applications/Text tools",
    "Documentation",
    "Office",
    "Networking/File transfer",
    "Networking/IRC",
    "Networking/ICQ",
    "Networking/Chat",
    "Networking/News",
    "Networking/Mail",
    "Networking/WWW",
    "Networking/Remote access",
    "Networking/Other",
    "Amusement/Adventure",
    "Amusement/Arcade",
    "Amusement/Boards",
    "Amusement/Cards",
    "Amusement/Puzzles",
    "Amusement/Sports",
    "Amusement/Strategy",
    "Amusement/Other",
    "Amusement/Toys",
    "Multimedia/Sound",
    "Multimedia/Graphics",
    "Multimedia/Video",
    "Session/Windowmanagers"
    )

DEFAULT_EXTRA_MENU_NEEDS = (
    "gnome",
    "icewm",
    "kde",
    "wmaker"
    )

DEFAULT_ICON_PATH = "/usr/share/icons/"

class MenuCheck(AbstractCheck.AbstractCheck):
    menu_file=re.compile("^/usr/lib/menu/([^/]+)$")
    old_menu_file=re.compile("^/usr/share/(gnome/apps|applnk)/([^/]+)$")
    package=re.compile("\?package\((.*)\):")
    needs=re.compile("needs=(\"([^\"]+)\"|([^ \t\"]+))")
    section=re.compile("section=(\"([^\"]+)\"|([^ \t\"]+))")
    title=re.compile("title=(\"([^\"]+)\"|([^ \t\"]+))")
    command=re.compile("command=\"?([^\" ]+)")
    kdesu_command=re.compile("[/usr/bin/]?kdesu -c \"?([^ \t\"]+)\"?")
    kdesu_bin=re.compile("[/usr/bin/]?kdesu")
    icon=re.compile("icon=\"?([^\" ]+)")
    valid_sections=Config.getOption("ValidMenuSections", DEFAULT_VALID_SECTIONS)
    update_menus=re.compile("^[^#]*update-menus",re.MULTILINE)
    standard_needs=Config.getOption("ExtraMenuNeeds", DEFAULT_EXTRA_MENU_NEEDS)
    xpm_icon_paths=Config.getOption("XpmIconPath", DEFAULT_ICON_PATH)
    xpm_ext=re.compile(xpm_icon_paths + ".*\.xpm$")
    
    def __init__(self):
        AbstractCheck.AbstractCheck.__init__(self, "MenuCheck")

    def check(self, pkg, verbose):
	# Check only binary package
	if pkg.isSource():
	    return

        files=pkg.files()
        pkgname=pkg[rpm.RPMTAG_NAME]
        menus=[]
        dirname=pkg.dirName()
        
        for f in files.keys():
            # Check menu files
            res=MenuCheck.menu_file.search(f)
            if res:
                basename=res.group(1)
                mode=files[f][0]
                if not stat.S_ISREG(mode):
                    printError(pkg, "non-file-in-menu-dir", f)
                else:
                    if basename != pkgname:
                        printWarning(pkg, "non-coherent-menu-filename", f)
                    menus.append(f)
            else:
                # Check old menus from KDE and GNOME
                res=MenuCheck.old_menu_file.search(f)
                if res:
                    mode=files[f][0]
                    if stat.S_ISREG(mode):
                        printError(pkg, "old-menu-entry", f)
                else:
                    # Check non transparent xpm files
                    res=MenuCheck.xpm_ext.search(f)
                    if res:
                        mode=files[f][0]
                        if stat.S_ISREG(mode) and not Pkg.grep("None\",", dirname + "/" + f):
                            printWarning(pkg, "non-transparent-xpm", f)
                            pass
        if len(menus) > 0:
            dir=pkg.dirName()
            if menus != []:
                postin=pkg[rpm.RPMTAG_POSTIN] or pkg[rpm.RPMTAG_POSTINPROG]
                if not postin:
                    printError(pkg, "menu-without-postin")
                else:
                    if not MenuCheck.update_menus.search(postin):
                        printError(pkg, "postin-without-update-menus")                    
                    
                postun=pkg[rpm.RPMTAG_POSTUN] or pkg[rpm.RPMTAG_POSTUNPROG]
                if not postun:
                    printError(pkg, "menu-without-postun")
                else:
                    if not MenuCheck.update_menus.search(postun):
                        printError(pkg, "postun-without-update-menus")

            for f in menus:
                # remove comments and handle cpp continuation lines
                str="/lib/cpp %s%s | grep ^\?" % (dir, f)
                cmd=commands.getoutput(str)
                for line in string.split(cmd, "\n"):
                    res=MenuCheck.package.search(line)
                    if res:
                        package=res.group(1)
                        if package != pkgname:
                            printWarning(pkg, "incoherent-package-value-in-menu", package, f)
                    else:
                        printInfo(pkg, "unable-to-parse-menu-entry", line)

                    command=1
                    res=MenuCheck.command.search(line)
                    if res:
                        command=res.group(1)
                        try:
                            if MenuCheck.kdesu_bin.search(command):
                                found=0
                                for i in pkg.requires() + pkg.prereq():
                                    if i[0] == "kdesu": found=1
                                if not found: printError(pkg, "use-of-kdesu-in-menu-but-not-in-requires")

                                res2=MenuCheck.kdesu_command.search(line)
                                command=res2.group(1)

                            if command[0] == '/':
                                files[command]
                            else:
                                if not (files.has_key("/bin/" + command) or
                                        files.has_key("/usr/bin/" + command) or
                                        files.has_key("/usr/X11R6/bin/" + command)):
                                    raise KeyError, command
                        except KeyError:
                            printWarning(pkg, "menu-command-not-in-package", command)
                    else:
                        command=0

                    res=MenuCheck.title.search(line)
                    if res:
                        grp=res.groups()
                        title=grp[1] or grp[2]
                    else:
                        printError(pkg, "no-title-in-menu", f)
                        title=None
                        
                    res=MenuCheck.needs.search(line)
                    if res:
                        grp=res.groups()
                        needs=string.lower(grp[1] or grp[2])
                        if needs in ("x11", "text" ,"wm"):
                            res=MenuCheck.section.search(line)
                            if res:
                                grp=res.groups()
                                section=grp[1] or grp[2]
                                # don't warn entries for sections
                                if command:
                                    if section not in MenuCheck.valid_sections:
                                        printError(pkg, "invalid-menu-section", section, f)
                            else:
                                printInfo(pkg, "unable-to-parse-menu-section", line)
                        elif needs not in MenuCheck.standard_needs:
                            printInfo(pkg, "strange-needs", needs, f)
                    else:
                        printInfo(pkg, "unable-to-parse-menu-needs", line)

                    res=MenuCheck.icon.search(line)
                    if res:
                        icon=res.group(1)
                        try:
                            if icon[0] == '/':
                                files[icon]
                        except KeyError:
                            printError(pkg, "specified-icon-not-in-package", icon, f)
                    else:
                        printWarning(pkg, "no-icon-in-menu", title)
                        
# Create an object to enable the auto registration of the test
check=MenuCheck()

# MenuCheck.py ends here
