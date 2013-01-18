# -*- coding: utf-8 -*-

#
# check xdg file format violation
#
# http://standards.freedesktop.org/desktop-entry-spec/desktop-entry-spec-latest.html
#

from Filter import addDetails, printError, printWarning
from Pkg import getstatusoutput, is_utf8
import AbstractCheck
from ConfigParser import RawConfigParser
import os

STANDARD_BIN_DIRS = ['/bin/','/sbin/','/usr/bin/','/usr/sbin/']

class MenuXDGCheck(AbstractCheck.AbstractFilesCheck):
    def __init__(self):
        # desktop file need to be in $XDG_DATA_DIRS
        # $ echo $XDG_DATA_DIRS/applications
        # /var/lib/menu-xdg:/usr/share
        self.cfp = RawConfigParser()
        AbstractCheck.AbstractFilesCheck.__init__(
            self, "MenuXDGCheck", "/usr/share/applications/.*\.desktop$")

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

        self.cfp.read(f)
        binary = self.cfp.get('Desktop Entry','Exec').split(' ',1)[0]
        found = False
        for i in STANDARD_BIN_DIRS:
            if os.path.exists(root + i + binary):
                # no need to check if the binary is +x, rpmlint does it
                # in another place
                found = True
        if not found and binary:
            printWarning(pkg, 'desktopfile-without-binary', filename, binary)

check = MenuXDGCheck()

addDetails(
'invalid-desktopfile',
'''.desktop file is not valid, check with desktop-file-validate''',

'non-utf8-desktopfile',
'''.desktop file is not encoded in UTF-8''',

'desktopfile-without-binary',
'''the .desktop file is for a file not present in the package. You
should check the requires or see if this is not a error''',
)

# Local variables:
# indent-tabs-mode: nil
# py-indent-offset: 4
# End:
# ex: ts=4 sw=4 et
