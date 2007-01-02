# Version         : $Id$

#
# check xdg file format violation
# 
# http://standards.freedesktop.org/desktop-entry-spec/desktop-entry-spec-latest.html
#

from Filter import *
from Pkg import getstatusoutput, is_utf8
import AbstractCheck
import Config

class MenuXDGCheck(AbstractCheck.AbstractFilesCheck):
    def __init__(self):
        # desktop file need to be in $XDG_DATA_DIRS
        # $ echo $XDG_DATA_DIRS/applications
        # /var/lib/menu-xdg:/usr/share
        AbstractCheck.AbstractFilesCheck.__init__(self, "MenuXDGCheck", "/usr/share/applications/.*\.desktop$")

    def check_file(self, pkg, filename):
        f = pkg.dirName() + filename
        if getstatusoutput(('desktop-file-validate', f), 1)[0]:
                printError(pkg, 'invalid-desktopfile', f)
        if not is_utf8(f):
                printError(pkg, 'non-utf8-desktopfile', f)
                

check=MenuXDGCheck()

if Config.info:
    addDetails(
        'invalid-desktopfile',
        '''.desktop file is not valid, check with desktop-file-validate''',
        'non-utf8-desktopfile',
        '''.desktop file is not encoded in UTF-8''',)

# Local variables:
# indent-tabs-mode: nil
# py-indent-offset: 4
# End:
# ex: ts=4 sw=4 et
