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
    'Office/Accessories',
    'Office/AddressBooks',
    'Office/Communications/Fax',
    'Office/Communications/PDA',
    'Office/Communications/Phone',
    'Office/Communication/Other',
    'Office/Drawing',
    'Office/Graphs',
    'Office/Presentations',
    'Office/Publishing',
    'Office/Spreadsheets',
    'Office/Tasks management',
    'Office/Time management',
    'Office/Wordprocessors',
    'Office/Other',
    'Internet/Chat',
    'Internet/File transfer',
    'Internet/Instant messaging',
    'Internet/Mail',
    'Internet/News',
    'Internet/Remote access',
    'Internet/Video Conference',
    'Internet/Web browsers',
    'Internet/Web editors',
    'Internet/Other',
    'Multimedia/Graphics',
    'Multimedia/Sound',
    'Multimedia/Video',
    'Multimedia/Other',
    'System/Archiving/Backup',
    'System/Archiving/Cd burning',
    'System/Archiving/Compression',
    'System/Archiving/Other',
    'System/Configuration/Boot and Init',
    'System/Configuration/GNOME',
    'System/Configuration/Hardware',
    'System/Configuration/KDE',
    'System/Configuration/Networking',
    'System/Configuration/Packaging',
    'System/Configuration/Printing',
    'System/Configuration/Users',
    'System/Configuration/Other'
    'System/File tools',
    'System/Monitoring',
    'System/Session/Windowmanagers',
    'System/Terminals',
    'System/Text tools',
    'System/Other',
    'More applications/Accessibility',
    'More applications/Communications',
    'More applications/Databases',
    'More applications/Development/Code generators',
    'More applications/Development/Development environments',
    'More applications/Development/Interpreters',
    'More applications/Development/Tools',
    'More applications/Development/Other',
    'More applications/Documentation',
    'More applications/Editors',
    'More applications/Education/Economy',
    'More applications/Education/Geography',
    'More applications/Education/History',
    'More applications/Education/Languages',
    'More applications/Education/Literature',
    'More applications/Education/Sciences',
    'More applications/Education/Sports',
    'More applications/Education/Other',
    'More applications/Emulators',
    'More applications/Finances',
    'More applications/Games/Adventure',
    'More applications/Games/Arcade',
    'More applications/Games/Boards',
    'More applications/Games/Cards',
    'More applications/Games/Puzzles',
    'More applications/Games/Sports',
    'More applications/Games/Strategy',
    'More applications/Games/Toys',
    'More applications/Games/Other',
    'More applications/Sciences/Artificial intelligence',
    'More applications/Sciences/Astronomy',
    'More applications/Sciences/Biology',
    'More applications/Sciences/Chemistry',
    'More applications/Sciences/Computer science',
    'More applications/Sciences/Data visualization',
    'More applications/Sciences/Electricity',
    'More applications/Sciences/Geosciences',
    'More applications/Sciences/Image processing',
    'More applications/Sciences/Mathematics',
    'More applications/Sciences/Numerical analysis',
    'More applications/Sciences/Parallel Computing',
    'More applications/Sciences/Physics',
    'More applications/Sciences/Robotics',
    'More applications/Sciences/Other',
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
icon_ext_regex=re.compile(Config.getOption('IconFilename', '.*\.png$'))
capital_regex=re.compile('[0-9A-Z]')
version_regex=re.compile('([0-9.][0-9.]+)($|\s)')
launchers=Config.getOption('MenuLaunchers', Config.DEFAULT_LAUNCHERS)
bad_title_regex=re.compile('/')

# compile regexps
for l in launchers:
    l[0]=re.compile(l[0])
    
class MenuCheck(AbstractCheck.AbstractCheck):
    
    def __init__(self):
        AbstractCheck.AbstractCheck.__init__(self, 'MenuCheck')

    def check(self, pkg):
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
                    if mode & 0111 != 0:
                        printError(pkg, 'executable-menu-file', f)
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
                        if bad_title_regex.search(title):
                            printError(pkg, 'invalid-title', title)
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
                        if not icon_ext_regex.search(icon):
                            printWarning(pkg, 'invalid-menu-icon-type', icon)
                        if icon[0] == '/' and needs == 'x11':
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
'''/usr/lib/menu must not contain something else than normal files.''',

'non-coherent-menu-filename',
'''The menu file name should be /usr/lib/menu/<package>.''',

'non-readable-menu-file',
'''The menu file isn't readable. Check the permissions.''',

'old-menu-entry',
'''
''',

'non-transparent-xpm',
'''xpm icon should be transparent to used in menus.''',

'menu-without-postin',
'''A menu file exists in the package but no %post is present to call
update-menus.''',

'postin-without-update-menus',
'''A menu file exists in the package but the %post doesn't call update-menus.''',

'menu-without-postun',
'''A menu file exists in the package but no %postun is present to call
update-menus.''',

'postun-without-update-menus',
'''A menu file exists in the package but the %postun doesn't call update-menus.''',

'incoherent-package-value-in-menu',
'''The package field of the menu entry isn't the same as the package name.''',

'use-of-launcher-in-menu-but-no-requires-on',
'''The menu command uses a launcher but there is no require on the package
that contains it.''',

'menu-command-not-in-package',
'''The command used in the menu isn't contained in the package.''',

'menu-longtitle-not-capitalized',
'''The longtitle field of the menu doesn't start with a capital letter.''',

'version-in-menu-longtitle',
'''A version is contained in the longtitle field of the menu entry. This is bad because
it will be prone to error when the version of the package changes.''',

'no-longtitle-in-menu',
'''The longtitle field isn't present in the menu entry.''',

'menu-title-not-capitalized',
'''The title field of the menu entry doesn't start with a capital letter.''',

'version-in-menu-title',
'''A version is contained in the title field of the menu entry. This is bad because
it will be prone to error when the version of the package changes.''',

'no-title-in-menu',
'''The title field isn't present in the menu entry.''',

'invalid-menu-section',
'''The section field of the menu entry isn't standard.''',

'unable-to-parse-menu-section',
'''rpmlint wasn't able to parse the menu section. Please report.''',

'hardcoded-path-in-menu-icon',
'''The path of the icon is hardcoded in the menu entry. This prevent multiple sizes
of the icon to be found.''',

'normal-icon-not-in-package',
'''The normal icon isn't present in the package.''',

'mini-icon-not-in-package',
'''The mini icon isn't present in the package.''',

'large-icon-not-in-package',
'''The large icon isn't present in the package.''',

'no-icon-in-menu',
'''The menu entry doesn't contain an icon field.''',

'invalid-title',
'''The menu title contains invalid characters like /.''',

)

# MenuCheck.py ends here
