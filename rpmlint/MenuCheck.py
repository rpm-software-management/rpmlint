# -*- coding: utf-8 -*-
#############################################################################
# Project         : Mandriva Linux
# Module          : rpmlint
# File            : MenuCheck.py
# Author          : Frederic Lepied
# Created On      : Mon Mar 20 07:43:37 2000
#############################################################################

import re
import stat

import rpm

import rpmlint.AbstractCheck as AbstractCheck
import rpmlint.Config as Config
import rpmlint.Pkg as Pkg
from rpmlint.Filter import addDetails, printError, printInfo, printWarning


DEFAULT_VALID_SECTIONS = (
    'Office/Accessories',
    'Office/Address Books',
    'Office/Communications/Fax',
    'Office/Communications/PDA',
    'Office/Communications/Phone',
    'Office/Communications/Other',
    'Office/Drawing',
    'Office/Graphs',
    'Office/Presentations',
    'Office/Publishing',
    'Office/Spreadsheets',
    'Office/Tasks Management',
    'Office/Time Management',
    'Office/Wordprocessors',
    'Office/Other',
    'Internet/Chat',
    'Internet/File Transfer',
    'Internet/Instant Messaging',
    'Internet/Mail',
    'Internet/News',
    'Internet/Remote Access',
    'Internet/Video Conference',
    'Internet/Web Browsers',
    'Internet/Web Editors',
    'Internet/Other',
    'Multimedia/Graphics',
    'Multimedia/Sound',
    'Multimedia/Video',
    'Multimedia/Other',
    'System/Archiving/Backup',
    'System/Archiving/CD Burning',
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
    'System/Configuration/Other',
    'System/File Tools',
    'System/Monitoring',
    'System/Session/Windowmanagers',
    'System/Terminals',
    'System/Text Tools',
    'System/Other',
    'More Applications/Accessibility',
    'More Applications/Communications',
    'More Applications/Databases',
    'More Applications/Development/Code Generators',
    'More Applications/Development/Development Environments',
    'More Applications/Development/Interpreters',
    'More Applications/Development/Tools',
    'More Applications/Development/Other',
    'More Applications/Documentation',
    'More Applications/Editors',
    'More Applications/Education/Economy',
    'More Applications/Education/Geography',
    'More Applications/Education/History',
    'More Applications/Education/Languages',
    'More Applications/Education/Literature',
    'More Applications/Education/Sciences',
    'More Applications/Education/Sports',
    'More Applications/Education/Other',
    'More Applications/Emulators',
    'More Applications/Finances',
    'More Applications/Games/Adventure',
    'More Applications/Games/Arcade',
    'More Applications/Games/Boards',
    'More Applications/Games/Cards',
    'More Applications/Games/Puzzles',
    'More Applications/Games/Sports',
    'More Applications/Games/Strategy',
    'More Applications/Games/Toys',
    'More Applications/Games/Other',
    'More Applications/Sciences/Artificial Intelligence',
    'More Applications/Sciences/Astronomy',
    'More Applications/Sciences/Biology',
    'More Applications/Sciences/Chemistry',
    'More Applications/Sciences/Computer Science',
    'More Applications/Sciences/Data visualization',
    'More Applications/Sciences/Electricity',
    'More Applications/Sciences/Geosciences',
    'More Applications/Sciences/Image Processing',
    'More Applications/Sciences/Mathematics',
    'More Applications/Sciences/Numerical Analysis',
    'More Applications/Sciences/Parallel Computing',
    'More Applications/Sciences/Physics',
    'More Applications/Sciences/Robotics',
    'More Applications/Sciences/Other',
    'More Applications/Other',
)

DEFAULT_EXTRA_MENU_NEEDS = (
    'gnome',
    'icewm',
    'kde',
    'wmaker',
)

DEFAULT_ICON_PATH = (
    ('/usr/share/icons/', 'normal'),
    ('/usr/share/icons/mini/', 'mini'),
    ('/usr/share/icons/large/', 'large'),
)

DEFAULT_LAUNCHERS = (
    ['(?:/usr/bin/)?kdesu', ('/usr/bin/kdesu', 'kdesu')],
    ['(?:/usr/bin/)?launch_x11_clanapp',
     ('/usr/bin/launch_x11_clanapp', 'clanlib', 'libclanlib0')],
    ['(?:/usr/bin/)?soundwrapper', None],
)

menu_file_regex = re.compile(r'^/usr/lib/menu/([^/]+)$')
old_menu_file_regex = re.compile(r'^/usr/share/(gnome/apps|applnk)/([^/]+)$')
package_regex = re.compile(r'\?package\((.*)\):')
needs_regex = re.compile(r'needs=(\"([^\"]+)\"|([^ %s\"]+))' % "\t")
section_regex = re.compile(r'section=(\"([^\"]+)\"|([^ %s\"]+))' % "\t")
title_regex = re.compile(r'[\"\s]title=(\"([^\"]+)\"|([^ %s\"]+))' % "\t")
longtitle_regex = re.compile(r'longtitle=(\"([^\"]+)\"|([^ %s\"]+))' % "\t")
command_regex = re.compile(r'command=(?:\"([^\"]+)\"|([^ %s\"]+))' % "\t")
icon_regex = re.compile(r'icon=\"?([^\" ]+)')
valid_sections = Config.getOption('ValidMenuSections', DEFAULT_VALID_SECTIONS)
update_menus_regex = re.compile(r'^[^#]*update-menus', re.MULTILINE)
standard_needs = Config.getOption('ExtraMenuNeeds', DEFAULT_EXTRA_MENU_NEEDS)
icon_paths = Config.getOption('IconPath', DEFAULT_ICON_PATH)
xpm_ext_regex = re.compile(r'/usr/share/icons/(mini/|large/).*\.xpm$')
icon_ext_regex = re.compile(Config.getOption('IconFilename', r'.*\.png$'))
version_regex = re.compile(r'([0-9.][0-9.]+)($|\s)')
launchers = Config.getOption('MenuLaunchers', DEFAULT_LAUNCHERS)
xdg_migrated_regex = re.compile(r'xdg=\"?([^\" ]+)')

# compile regexps
for l in launchers:
    l[0] = re.compile(l[0])
del l


class MenuCheck(AbstractCheck.AbstractCheck):

    def __init__(self):
        AbstractCheck.AbstractCheck.__init__(self, 'MenuCheck')

    def check_binary(self, pkg):
        files = pkg.files()
        menus = []

        for fname, pkgfile in files.items():
            # Check menu files
            res = menu_file_regex.search(fname)
            mode = pkgfile.mode
            if res:
                basename = res.group(1)
                if not stat.S_ISREG(mode):
                    printError(pkg, 'non-file-in-menu-dir', fname)
                else:
                    if basename != pkg.name:
                        printWarning(pkg, 'non-coherent-menu-filename', fname)
                    if mode & 0o444 != 0o444:
                        printError(pkg, 'non-readable-menu-file', fname)
                    if mode & 0o111:
                        printError(pkg, 'executable-menu-file', fname)
                    menus.append(fname)
            else:
                # Check old menus from KDE and GNOME
                res = old_menu_file_regex.search(fname)
                if res:
                    if stat.S_ISREG(mode):
                        printError(pkg, 'old-menu-entry', fname)
                else:
                    # Check non transparent xpm files
                    res = xpm_ext_regex.search(fname)
                    if res:
                        if stat.S_ISREG(mode) and not pkg.grep('None",', fname):
                            printWarning(pkg, 'non-transparent-xpm', fname)
                if fname.startswith('/usr/lib64/menu'):
                    printError(pkg, 'menu-in-wrong-dir', fname)

        if menus:
            postin = pkg[rpm.RPMTAG_POSTIN] or \
                pkg.scriptprog(rpm.RPMTAG_POSTINPROG)
            if not postin:
                printError(pkg, 'menu-without-postin')
            elif not update_menus_regex.search(postin):
                printError(pkg, 'postin-without-update-menus')

            postun = pkg[rpm.RPMTAG_POSTUN] or \
                pkg.scriptprog(rpm.RPMTAG_POSTUNPROG)
            if not postun:
                printError(pkg, 'menu-without-postun')
            elif not update_menus_regex.search(postun):
                printError(pkg, 'postun-without-update-menus')

            directory = pkg.dirName()
            for f in menus:
                # remove comments and handle cpp continuation lines
                cmd = Pkg.getstatusoutput(('/lib/cpp', directory + f), True)[1]

                for line in cmd.splitlines():
                    if not line.startswith('?'):
                        continue
                    res = package_regex.search(line)
                    if res:
                        package = res.group(1)
                        if package != pkg.name:
                            printWarning(pkg,
                                         'incoherent-package-value-in-menu',
                                         package, f)
                    else:
                        printInfo(pkg, 'unable-to-parse-menu-entry', line)

                    command = True
                    res = command_regex.search(line)
                    if res:
                        command_line = (res.group(1) or res.group(2)).split()
                        command = command_line[0]
                        for launcher in launchers:
                            if not launcher[0].search(command):
                                continue
                            found = False
                            if launcher[1]:
                                found = '/bin/' + command_line[0] in files or \
                                    '/usr/bin/' + command_line[0] in files or \
                                    '/usr/X11R6/bin/' + command_line[0] \
                                    in files
                                if not found:
                                    for l in launcher[1]:
                                        if l in pkg.req_names():
                                            found = True
                                            break
                                if not found:
                                    printError(pkg,
                                               'use-of-launcher-in-menu-but-no-requires-on',
                                               launcher[1][0])
                            command = command_line[1]
                            break

                        if command[0] == '/':
                            if command not in files:
                                printWarning(
                                    pkg, 'menu-command-not-in-package',
                                    command)
                        elif not ('/bin/' + command in files or
                                  '/usr/bin/' + command in files or
                                  '/usr/X11R6/bin/' + command in files):
                            printWarning(pkg, 'menu-command-not-in-package',
                                         command)
                    else:
                        printWarning(pkg, 'missing-menu-command')
                        command = False

                    res = longtitle_regex.search(line)
                    if res:
                        grp = res.groups()
                        title = grp[1] or grp[2]
                        if title[0] != title[0].upper():
                            printWarning(pkg, 'menu-longtitle-not-capitalized',
                                         title)
                        res = version_regex.search(title)
                        if res:
                            printWarning(pkg, 'version-in-menu-longtitle',
                                         title)
                    else:
                        printError(pkg, 'no-longtitle-in-menu', f)
                        title = None

                    res = title_regex.search(line)
                    if res:
                        grp = res.groups()
                        title = grp[1] or grp[2]
                        if title[0] != title[0].upper():
                            printWarning(pkg, 'menu-title-not-capitalized',
                                         title)
                        res = version_regex.search(title)
                        if res:
                            printWarning(pkg, 'version-in-menu-title', title)
                        if '/' in title:
                            printError(pkg, 'invalid-title', title)
                    else:
                        printError(pkg, 'no-title-in-menu', f)
                        title = None

                    res = needs_regex.search(line)
                    if res:
                        grp = res.groups()
                        needs = (grp[1] or grp[2]).lower()
                        if needs in ('x11', 'text', 'wm'):
                            res = section_regex.search(line)
                            if res:
                                grp = res.groups()
                                section = grp[1] or grp[2]
                                # don't warn entries for sections
                                if command and section not in valid_sections:
                                    printError(pkg, 'invalid-menu-section',
                                               section, f)
                            else:
                                printInfo(pkg, 'unable-to-parse-menu-section',
                                          line)
                        elif needs not in standard_needs:
                            printInfo(pkg, 'strange-needs', needs, f)
                    else:
                        printInfo(pkg, 'unable-to-parse-menu-needs', line)

                    res = icon_regex.search(line)
                    if res:
                        icon = res.group(1)
                        if not icon_ext_regex.search(icon):
                            printWarning(pkg, 'invalid-menu-icon-type', icon)
                        if icon[0] == '/' and needs == 'x11':
                            printWarning(pkg, 'hardcoded-path-in-menu-icon',
                                         icon)
                        else:
                            for path in icon_paths:
                                if (path[0] + icon) not in files:
                                    printError(
                                        pkg, path[1] + '-icon-not-in-package',
                                        icon, f)
                    else:
                        printWarning(pkg, 'no-icon-in-menu', title)

                    res = xdg_migrated_regex.search(line)
                    if res:
                        if not res.group(1).lower() == "true":
                            printError(pkg, 'non-xdg-migrated-menu')
                    else:
                        printError(pkg, 'non-xdg-migrated-menu')


# Create an object to enable the auto registration of the test
check = MenuCheck()

addDetails(
'non-file-in-menu-dir',
'''/usr/lib/menu must not contain anything else than normal files.''',

'non-coherent-menu-filename',
'''The menu file name should be /usr/lib/menu/<package>.''',

'non-readable-menu-file',
'''The menu file isn't readable. Check the permissions.''',

'old-menu-entry',
'''
''',

'non-transparent-xpm',
'''xpm icon should be transparent for use in menus.''',

'menu-without-postin',
'''A menu file exists in the package but no %post scriptlet is present to call
update-menus.''',

'postin-without-update-menus',
'''A menu file exists in the package but its %post scriptlet doesn't call
update-menus.''',

'menu-without-postun',
'''A menu file exists in the package but no %postun scriptlet is present to
call update-menus.''',

'postun-without-update-menus',
'''A menu file exists in the package but its %postun scriptlet doesn't call
update-menus.''',

'incoherent-package-value-in-menu',
'''The package field of the menu entry isn't the same as the package name.''',

'use-of-launcher-in-menu-but-no-requires-on',
'''The menu command uses a launcher but there is no dependency in the package
that contains it.''',

'menu-command-not-in-package',
'''The command used in the menu isn't included in the package.''',

'menu-longtitle-not-capitalized',
'''The longtitle field of the menu doesn't start with a capital letter.''',

'version-in-menu-longtitle',
'''The longtitle filed of the menu entry contains a version. This is bad
because it will be prone to error when the version of the package changes.''',

'no-longtitle-in-menu',
'''The longtitle field isn't present in the menu entry.''',

'menu-title-not-capitalized',
'''The title field of the menu entry doesn't start with a capital letter.''',

'version-in-menu-title',
'''The title filed of the menu entry contains a version. This is bad
because it will be prone to error when the version of the package changes.''',

'no-title-in-menu',
'''The title field isn't present in the menu entry.''',

'invalid-menu-section',
'''The section field of the menu entry isn't standard.''',

'unable-to-parse-menu-section',
'''rpmlint wasn't able to parse the menu section. Please report.''',

'hardcoded-path-in-menu-icon',
'''The path of the icon is hardcoded in the menu entry. This prevent multiple
sizes of the icon from being found.''',

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

'missing-menu-command',
'''The menu file doesn't contain a command.''',

'menu-in-wrong-directory',
'''The menu files must be under /usr/lib/menu.''',

'non-xdg-migrated-menu',
'''The menu file has not been migrated to new XDG menu system.''',

)

# MenuCheck.py ends here
