# -*- coding: utf-8 -*-
# Version         : $Id$

#
# check xdg file format violation
#
# http://standards.freedesktop.org/desktop-entry-spec/desktop-entry-spec-latest.html
#

from Filter import addDetails, printError
from Pkg import getstatusoutput, is_utf8
import AbstractCheck


class MenuXDGCheck(AbstractCheck.AbstractFilesCheck):
    def __init__(self):
        # desktop file need to be in $XDG_DATA_DIRS
        # $ echo $XDG_DATA_DIRS/applications
        # /var/lib/menu-xdg:/usr/share
        AbstractCheck.AbstractFilesCheck.__init__(self, "MenuXDGCheck", "/usr/share/applications/.*\.desktop$")

    def check_file(self, pkg, filename):
        f = pkg.dirName() + filename
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


check = MenuXDGCheck()

addDetails(
'invalid-desktopfile',
'''.desktop file is not valid, check with desktop-file-validate''',

'non-utf8-desktopfile',
'''.desktop file is not encoded in UTF-8''',
)

# Local variables:
# indent-tabs-mode: nil
# py-indent-offset: 4
# End:
# ex: ts=4 sw=4 et
