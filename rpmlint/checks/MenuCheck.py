#############################################################################
# Project         : Mandriva Linux
# Module          : rpmlint
# File            : MenuCheck.py
# Author          : Frederic Lepied
# Created On      : Mon Mar 20 07:43:37 2000
#############################################################################

import re
import stat
import subprocess

import rpm
from rpmlint.checks.AbstractCheck import AbstractCheck
from rpmlint.helpers import ENGLISH_ENVIROMENT


menu_file_regex = re.compile(r'^/usr/lib/menu/([^/]+)$')
old_menu_file_regex = re.compile(r'^/usr/share/(gnome/apps|applnk)/([^/]+)$')
package_regex = re.compile(r'\?package\((.*)\):')
needs_regex = re.compile(r'needs=(\"([^\"]+)\"|([^ %s\"]+))' % '\t')
section_regex = re.compile(r'section=(\"([^\"]+)\"|([^ %s\"]+))' % '\t')
title_regex = re.compile(r'[\"\s]title=(\"([^\"]+)\"|([^ %s\"]+))' % '\t')
longtitle_regex = re.compile(r'longtitle=(\"([^\"]+)\"|([^ %s\"]+))' % '\t')
command_regex = re.compile(r'command=(?:\"([^\"]+)\"|([^ %s\"]+))' % '\t')
icon_regex = re.compile(r'icon=\"?([^\" ]+)')
update_menus_regex = re.compile(r'^[^#]*update-menus', re.MULTILINE)
xpm_ext_regex = re.compile(r'/usr/share/icons/(mini/|large/).*\.xpm$')
version_regex = re.compile(r'([0-9.][0-9.]+)($|\s)')
xdg_migrated_regex = re.compile(r'xdg=\"?([^\" ]+)')


class MenuCheck(AbstractCheck):

    def __init__(self, config, output):
        super().__init__(config, output)
        self.valid_sections = self.config.configuration['ValidMenuSections']
        self.standard_needs = self.config.configuration['ExtraMenuNeeds']
        self.icon_paths = self.config.configuration['IconPath']
        self.launchers = self.config.configuration['MenuLaunchers']
        self.icon_ext_regex = re.compile(self.config.configuration['IconFilename'])
        # compile regexps
        for value in self.launchers.values():
            value['regexp'] = re.compile(value['regexp'])

    def check_binary(self, pkg):
        files = pkg.files
        menus = []

        for fname, pkgfile in files.items():
            # Check menu files
            res = menu_file_regex.search(fname)
            mode = pkgfile.mode
            if res:
                basename = res.group(1)
                if not stat.S_ISREG(mode):
                    self.output.add_info('E', pkg, 'non-file-in-menu-dir', fname)
                else:
                    if basename != pkg.name:
                        self.output.add_info('W', pkg, 'non-coherent-menu-filename', fname)
                    if mode & 0o444 != 0o444:
                        self.output.add_info('E', pkg, 'non-readable-menu-file', fname)
                    if mode & 0o111:
                        self.output.add_info('E', pkg, 'executable-menu-file', fname)
                    menus.append(fname)
            else:
                # Check old menus from KDE and GNOME
                res = old_menu_file_regex.search(fname)
                if res:
                    if stat.S_ISREG(mode):
                        self.output.add_info('E', pkg, 'old-menu-entry', fname)
                else:
                    # Check non transparent xpm files
                    res = xpm_ext_regex.search(fname)
                    if res:
                        if stat.S_ISREG(mode) and not pkg.grep('None",', fname):
                            self.output.add_info('W', pkg, 'non-transparent-xpm', fname)
                if fname.startswith('/usr/lib64/menu'):
                    self.output.add_info('E', pkg, 'menu-in-wrong-dir', fname)

        if menus:
            postin = pkg[rpm.RPMTAG_POSTIN] or \
                pkg.scriptprog(rpm.RPMTAG_POSTINPROG)
            if not postin:
                self.output.add_info('E', pkg, 'menu-without-postin')
            elif not update_menus_regex.search(postin):
                self.output.add_info('E', pkg, 'postin-without-update-menus')

            postun = pkg[rpm.RPMTAG_POSTUN] or \
                pkg.scriptprog(rpm.RPMTAG_POSTUNPROG)
            if not postun:
                self.output.add_info('E', pkg, 'menu-without-postun')
            elif not update_menus_regex.search(postun):
                self.output.add_info('E', pkg, 'postun-without-update-menus')

            directory = pkg.dirName()
            for f in menus:
                # remove comments and handle cpp continuation lines
                text = subprocess.run(('/lib/cpp', directory + f), stdout=subprocess.PIPE, stderr=subprocess.STDOUT, env=ENGLISH_ENVIROMENT).stdout.decode()
                if text.endswith('\n'):
                    text = text[:-1]

                for line in text.splitlines():
                    if not line.startswith('?'):
                        continue
                    res = package_regex.search(line)
                    if res:
                        package = res.group(1)
                        if package != pkg.name:
                            self.output.add_info('W', pkg,
                                                 'incoherent-package-value-in-menu',
                                                 package, f)
                    else:
                        self.output.add_info('I', pkg, 'unable-to-parse-menu-entry', line)

                    command = True
                    res = command_regex.search(line)
                    if res:
                        command_line = (res.group(1) or res.group(2)).split()
                        command = command_line[0]
                        for launcher in self.launchers.values():
                            if not launcher['regexp'].search(command):
                                continue
                            found = False
                            if launcher['binaries']:
                                found = '/bin/' + command_line[0] in files or \
                                    '/usr/bin/' + command_line[0] in files or \
                                    '/usr/X11R6/bin/' + command_line[0] \
                                    in files
                                if not found:
                                    for i in launcher['binaries']:
                                        if i in pkg.req_names:
                                            found = True
                                            break
                                if not found:
                                    self.output.add_info('E', pkg,
                                                         'use-of-launcher-in-menu-but-no-requires-on',
                                                         launcher['binaries'][0])
                            command = command_line[1]
                            break

                        if command[0] == '/':
                            if command not in files:
                                self.output.add_info('W',
                                                     pkg, 'menu-command-not-in-package',
                                                     command)
                        elif not ('/bin/' + command in files or
                                  '/usr/bin/' + command in files or
                                  '/usr/X11R6/bin/' + command in files):
                            self.output.add_info('W', pkg, 'menu-command-not-in-package',
                                                 command)
                    else:
                        self.output.add_info('W', pkg, 'missing-menu-command')
                        command = False

                    res = longtitle_regex.search(line)
                    if res:
                        grp = res.groups()
                        title = grp[1] or grp[2]
                        if title[0] != title[0].upper():
                            self.output.add_info('W', pkg, 'menu-longtitle-not-capitalized',
                                                 title)
                        res = version_regex.search(title)
                        if res:
                            self.output.add_info('W', pkg, 'version-in-menu-longtitle',
                                                 title)
                    else:
                        self.output.add_info('E', pkg, 'no-longtitle-in-menu', f)
                        title = None

                    res = title_regex.search(line)
                    if res:
                        grp = res.groups()
                        title = grp[1] or grp[2]
                        if title[0] != title[0].upper():
                            self.output.add_info('W', pkg, 'menu-title-not-capitalized',
                                                 title)
                        res = version_regex.search(title)
                        if res:
                            self.output.add_info('W', pkg, 'version-in-menu-title', title)
                        if '/' in title:
                            self.output.add_info('E', pkg, 'invalid-title', title)
                    else:
                        self.output.add_info('E', pkg, 'no-title-in-menu', f)
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
                                if command and section not in self.valid_sections:
                                    self.output.add_info('E', pkg, 'invalid-menu-section',
                                                         section, f)
                            else:
                                self.output.add_info('I', pkg, 'unable-to-parse-menu-section',
                                                     line)
                        elif needs not in self.standard_needs:
                            self.output.add_info('I', pkg, 'strange-needs', needs, f)
                    else:
                        self.output.add_info('I', pkg, 'unable-to-parse-menu-needs', line)

                    res = icon_regex.search(line)
                    if res:
                        icon = res.group(1)
                        if not self.icon_ext_regex.search(icon):
                            self.output.add_info('W', pkg, 'invalid-menu-icon-type', icon)
                        if icon[0] == '/' and needs == 'x11':
                            self.output.add_info('W', pkg, 'hardcoded-path-in-menu-icon',
                                                 icon)
                        else:
                            for value in self.icon_paths.values():
                                if (value['path'] + icon) not in files:
                                    self.output.add_info('E',
                                                         pkg, value['type'] + '-icon-not-in-package',
                                                         icon, f)
                    else:
                        self.output.add_info('W', pkg, 'no-icon-in-menu', title)

                    res = xdg_migrated_regex.search(line)
                    if res:
                        if not res.group(1).lower() == 'true':
                            self.output.add_info('E', pkg, 'non-xdg-migrated-menu')
                    else:
                        self.output.add_info('E', pkg, 'non-xdg-migrated-menu')
