# -*- coding: utf-8 -*-

#
# check xdg file format violation
#
# http://standards.freedesktop.org/desktop-entry-spec/desktop-entry-spec-latest.html
#

import codecs
import os
try:
    import ConfigParser as cfgparser
except ImportError:
    import configparser as cfgparser

import rpmlint.AbstractCheck as AbstractCheck
from rpmlint.Filter import addDetails, printError, printWarning
from rpmlint.Pkg import getstatusoutput, is_utf8

STANDARD_BIN_DIRS = ('/bin', '/sbin', '/usr/bin', '/usr/sbin')


class MenuXDGCheck(AbstractCheck.AbstractFilesCheck):
    def __init__(self):
        # desktop file need to be in $XDG_DATA_DIRS
        # $ echo $XDG_DATA_DIRS/applications
        # /var/lib/menu-xdg:/usr/share
        AbstractCheck.AbstractFilesCheck.__init__(
            self, "MenuXDGCheck", r'(?:/usr|/etc/opt|/opt/.*)/share/applications/.*\.desktop$')

    def parse_desktop_file(self, pkg, root, f, filename):
        cfp = cfgparser.RawConfigParser()
        try:
            with codecs.open(f, encoding='utf-8') as inputf:
                cfp.readfp(inputf, filename)
        except cfgparser.DuplicateSectionError as e:
            printError(
                pkg, 'desktopfile-duplicate-section', filename,
                '[%s]' % e.section)
        except cfgparser.MissingSectionHeaderError:
            printError(
                pkg, 'desktopfile-missing-header', filename)
        except cfgparser.Error as e:
            # Only in Python >= 3.2
            if (hasattr(cfgparser, 'DuplicateOptionError') and
                    isinstance(e, cfgparser.DuplicateOptionError)):
                printError(
                    pkg, 'desktopfile-duplicate-option', filename,
                    '[%s]/%s' % (e.section, e.option))
            else:
                printWarning(
                    pkg, 'invalid-desktopfile', filename,
                    e.message.partition(':')[0])
        except UnicodeDecodeError as e:
            printWarning(
                pkg, 'invalid-desktopfile', filename, 'Unicode error: %s' % (e))
        else:
            binary = None
            if cfp.has_option('Desktop Entry', 'Exec'):
                binary = cfp.get('Desktop Entry', 'Exec').partition(' ')[0]
            if binary:
                found = False
                if binary.startswith('/'):
                    found = os.path.exists(root + binary)
                else:
                    for i in STANDARD_BIN_DIRS:
                        if os.path.exists(root + i + '/' + binary):
                            # no need to check if the binary is +x, rpmlint does it
                            # in another place
                            found = True
                            break
                if not found:
                    printWarning(
                        pkg, 'desktopfile-without-binary', filename, binary)

    def check_file(self, pkg, filename):
        root = pkg.dirName()
        f = root + filename
        st = getstatusoutput(('desktop-file-validate', f), True)
        if st[0]:
            error_printed = False
            for line in st[1].splitlines():
                if 'error: ' in line:
                    printError(pkg, 'invalid-desktopfile', filename,
                               line.split('error: ')[1])
                    error_printed = True
            if not error_printed:
                printError(pkg, 'invalid-desktopfile', filename)
        if not is_utf8(f):
            printError(pkg, 'non-utf8-desktopfile', filename)

        self.parse_desktop_file(pkg, root, f, filename)


check = MenuXDGCheck()

addDetails(
'invalid-desktopfile',
'''.desktop file is not valid, check with desktop-file-validate''',

'non-utf8-desktopfile',
'''.desktop file is not encoded in UTF-8''',

'desktopfile-without-binary',
'''the .desktop file is for a file not present in the package. You
should check the requires or see if this is not a error''',

'desktopfile-duplicate-section',
'''The .desktop file contains the mentioned section name twice, which
can trigger parsing ambiguities. Remove the duplicate.''',

'desktopfile-duplicate-option',
'''The .desktop file contains the mentioned option key twice,
which can trigger parsing ambiguities. Remove the duplicate.''',

'desktopfile-missing-header',
'''The .desktop file should start with a section header.''',
)
