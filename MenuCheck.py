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
    'Configuration/Hardware',
    'Configuration/Packaging',
    'Configuration/Networking',
    'Configuration/Printing',
    'Configuration/Boot and Init',
    'Configuration/Other',
    'Applications/Accessibility',
    'Applications/Development/Interpreters',
    'Applications/Development/Code generators',
    'Applications/Development/Development environments',
    'Applications/Development/Tools',
    'Applications/Sciences/Astronomy',
    'Applications/Sciences/Biology',
    'Applications/Sciences/Chemistry',
    'Applications/Sciences/Computer science',
    'Applications/Sciences/Geosciences',
    'Applications/Sciences/Mathematics',
    'Applications/Sciences/Physics',
    'Applications/Sciences/Other',
    'Applications/Communications',
    'Applications/Editors',
    'Applications/Emulators',
    'Applications/Archiving/Compression',
    'Applications/Archiving/Cd burning',
    'Applications/Archiving/Backup',
    'Applications/Archiving/Other',
    'Applications/Monitoring',
    'Applications/Publishing',
    'Terminals',
    'Applications/Shells',
    'Applications/File tools',
    'Applications/Text tools',
    'Documentation',
    'Office/Wordprocessors',
    'Office/Spreadsheets',
    'Office/Time management',
    'Office/AddressBooks',
    'Office/Presentations',
    'Office/Graphs',
    'Office/PDA',
    'Networking/File transfer',
    'Networking/IRC',
    'Networking/Instant messaging',
    'Networking/Chat',
    'Networking/News',
    'Networking/Mail',
    'Networking/WWW',
    'Networking/Remote access',
    'Networking/Other',
    'Amusement/Adventure',
    'Amusement/Arcade',
    'Amusement/Boards',
    'Amusement/Cards',
    'Amusement/Puzzles',
    'Amusement/Sports',
    'Amusement/Strategy',
    'Amusement/Other',
    'Amusement/Toys',
    'Multimedia/Sound',
    'Multimedia/Graphics',
    'Multimedia/Video',
    'Session/Windowmanagers'
    )

DEFAULT_EXTRA_MENU_NEEDS = (
    'gnome',
    'icewm',
    'kde',
    'wmaker'
    )

DEFAULT_ICON_PATH = (('/usr/share/icons/', 'normal'),
                     ('/usr/share/icons/mini/', 'mini'),
                     ('/usr/share/icons/large/', 'large'))

DEFAULT_LAUNCHERS = (['(?:/usr/bin/)?kdesu', ('/usr/bin/kdesu', 'kdesu')],
                     ['(?:/usr/bin/)?launch_x11_clanapp', ('/usr/bin/launch_x11_clanapp', 'clanlib', 'libclanlib0')],
                     ['(?:/usr/bin/)?soundwrapper', None],
                     ['NO_XALF', None],
                     )

menu_file_regex=re.compile('^/usr/lib/menu/([^/]+)$')
old_menu_file_regex=re.compile('^/usr/share/(gnome/apps|applnk)/([^/]+)$')
package_regex=re.compile('\?package\((.*)\):')
needs_regex=re.compile('needs=(\"([^\"]+)\"|([^ \t\"]+))')
section_regex=re.compile('section=(\"([^\"]+)\"|([^ \t\"]+))')
title_regex=re.compile('[\"\s]title=(\"([^\"]+)\"|([^ \t\"]+))')
longtitle_regex=re.compile('longtitle=(\"([^\"]+)\"|([^ \t\"]+))')
command_regex=re.compile('command=(?:\"([^\"]+)\"|([^ \t\"]+))')
kdesu_command_regex=re.compile('[/usr/bin/]?kdesu -c \"?([^ \t\"]+)\"?')
kdesu_bin_regex=re.compile('[/usr/bin/]?kdesu')
icon_regex=re.compile('icon=\"?([^\" ]+)')
valid_sections=Config.getOption('ValidMenuSections', DEFAULT_VALID_SECTIONS)
update_menus_regex=re.compile('^[^#]*update-menus',re.MULTILINE)
standard_needs=Config.getOption('ExtraMenuNeeds', DEFAULT_EXTRA_MENU_NEEDS)
icon_paths=Config.getOption('IconPath', DEFAULT_ICON_PATH)
xpm_ext_regex=re.compile('/usr/share/icons/(mini/|large/).*\.xpm$')
capital_regex=re.compile('[0-9A-Z]')
version_regex=re.compile('([0-9.][0-9.]+)($|\s)')
launchers=Config.getOption('MenuLaunchers', DEFAULT_LAUNCHERS)

# compile regexps
for l in launchers:
    l[0]=re.compile(l[0])
    
class MenuCheck(AbstractCheck.AbstractCheck):
    
    def __init__(self):
        AbstractCheck.AbstractCheck.__init__(self, 'MenuCheck')

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
            res=menu_file_regex.search(f)
            if res:
                basename=res.group(1)
                mode=files[f][0]
                if not stat.S_ISREG(mode):
                    printError(pkg, 'non-file-in-menu-dir', f)
                else:
                    if basename != pkgname:
                        printWarning(pkg, 'non-coherent-menu-filename', f)
                    if mode & 0444 != 0444:
                        printError(pkg, 'non-readable-menu-file', f)
                    menus.append(f)
            else:
                # Check old menus from KDE and GNOME
                res=old_menu_file_regex.search(f)
                if res:
                    mode=files[f][0]
                    if stat.S_ISREG(mode):
                        printError(pkg, 'old-menu-entry', f)
                else:
                    # Check non transparent xpm files
                    res=xpm_ext_regex.search(f)
                    if res:
                        mode=files[f][0]
                        if stat.S_ISREG(mode) and not Pkg.grep('None",', dirname + '/' + f):
                            printWarning(pkg, 'non-transparent-xpm', f)
        if len(menus) > 0:
            dir=pkg.dirName()
            if menus != []:
                postin=pkg[rpm.RPMTAG_POSTIN] or pkg[rpm.RPMTAG_POSTINPROG]
                if not postin:
                    printError(pkg, 'menu-without-postin')
                else:
                    if not update_menus_regex.search(postin):
                        printError(pkg, 'postin-without-update-menus')                    
                    
                postun=pkg[rpm.RPMTAG_POSTUN] or pkg[rpm.RPMTAG_POSTUNPROG]
                if not postun:
                    printError(pkg, 'menu-without-postun')
                else:
                    if not update_menus_regex.search(postun):
                        printError(pkg, 'postun-without-update-menus')

            for f in menus:
                # remove comments and handle cpp continuation lines
                str='/lib/cpp %s%s 2>/dev/null| grep ^\?' % (dir, f)
                cmd=commands.getoutput(str)
                for line in string.split(cmd, '\n'):
                    res=package_regex.search(line)
                    if res:
                        package=res.group(1)
                        if package != pkgname:
                            printWarning(pkg, 'incoherent-package-value-in-menu', package, f)
                    else:
                        printInfo(pkg, 'unable-to-parse-menu-entry', line)

                    command=1
                    res=command_regex.search(line)
                    if res:
                        command_line=string.split(res.group(1) or res.group(2))
                        command=command_line[0]
                        for launcher in launchers:
                            if launcher[0].search(command):
                                found=0
                                if launcher[1]:
                                    if (files.has_key('/bin/' + command_line[0]) or
                                        files.has_key('/usr/bin/' + command_line[0]) or
                                        files.has_key('/usr/X11R6/bin/' + command_line[0])):
                                        found=1
                                    else:
                                        for l in launcher[1]:
                                            if l in pkg.req_names():
                                                found=1
                                                break
                                    if not found:
                                        printError(pkg, 'use-of-launcher-in-menu-but-no-requires-on', launcher[1][0])
                                command=command_line[1]
                                break
                        try:
                            if command[0] == '/':
                                files[command]
                            else:
                                if not (files.has_key('/bin/' + command) or
                                        files.has_key('/usr/bin/' + command) or
                                        files.has_key('/usr/X11R6/bin/' + command)):
                                    raise KeyError, command
                        except KeyError:
                            printWarning(pkg, 'menu-command-not-in-package', command)
                    else:
                        command=0

                    res=longtitle_regex.search(line)
                    if res:
                        grp=res.groups()
                        title=grp[1] or grp[2]
                        if not capital_regex.search(title[0]):
                            printWarning(pkg, 'menu-longtitle-not-capitalized', title)
                        res=version_regex.search(title)
                        if res:
                            printWarning(pkg, 'version-in-menu-longtitle', title)
                    else:
                        printError(pkg, 'no-longtitle-in-menu', f)
                        title=None
                        
                    res=title_regex.search(line)
                    if res:
                        grp=res.groups()
                        title=grp[1] or grp[2]
                        if not capital_regex.search(title[0]):
                            printWarning(pkg, 'menu-title-not-capitalized', title)
                        res=version_regex.search(title)
                        if res:
                            printWarning(pkg, 'version-in-menu-title', title)
                    else:
                        printError(pkg, 'no-title-in-menu', f)
                        title=None
                        
                    res=needs_regex.search(line)
                    if res:
                        grp=res.groups()
                        needs=string.lower(grp[1] or grp[2])
                        if needs in ('x11', 'text' ,'wm'):
                            res=section_regex.search(line)
                            if res:
                                grp=res.groups()
                                section=grp[1] or grp[2]
                                # don't warn entries for sections
                                if command:
                                    if section not in valid_sections:
                                        printError(pkg, 'invalid-menu-section', section, f)
                            else:
                                printInfo(pkg, 'unable-to-parse-menu-section', line)
                        elif needs not in standard_needs:
                            printInfo(pkg, 'strange-needs', needs, f)
                    else:
                        printInfo(pkg, 'unable-to-parse-menu-needs', line)

                    res=icon_regex.search(line)
                    if res:
                        icon=res.group(1)
                        if icon[0] == '/':
                            printWarning(pkg, 'hardcoded-path-in-menu-icon', icon)
                        else:
                            for path in icon_paths:
                                try:
                                    files[path[0] + icon]
                                except KeyError:
                                    printError(pkg, path[1] + '-icon-not-in-package', icon, f)
                    else:
                        printWarning(pkg, 'no-icon-in-menu', title)
                        
# Create an object to enable the auto registration of the test
check=MenuCheck()

if Config.info:
    addDetails(
'non-file-in-menu-dir',
"""
""",

'non-coherent-menu-filename',
"""
""",

'non-readable-menu-file',
"""
""",

'old-menu-entry',
"""
""",

'non-transparent-xpm',
"""
""",

'menu-without-postin',
"""
""",

'postin-without-update-menus',
"""
""",

'menu-without-postun',
"""
""",

'postun-without-update-menus',
"""
""",

'incoherent-package-value-in-menu',
"""
""",

'use-of-launcher-in-menu-but-no-requires-on',
"""
""",

'menu-command-not-in-package',
"""
""",

'menu-longtitle-not-capitalized',
"""
""",

'version-in-menu-longtitle'
"""
""",

'no-longtitle-in-menu',
"""
""",

'menu-title-not-capitalized',
"""
""",

'version-in-menu-title',
"""
""",

'no-title-in-menu',
"""
""",

'invalid-menu-section',
"""
""",

'unable-to-parse-menu-section',
"""
""",

'hardcoded-path-in-menu-icon',
"""
""",

'-icon-not-in-package',
"""
""",

'no-icon-in-menu',
"""
""",

)

# MenuCheck.py ends here
