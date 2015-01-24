# -*- coding: utf-8 -*-

#
# check appdata file format violation
#
# http://people.freedesktop.org/~hughsient/appdata/
#

from Filter import addDetails, printError
from Pkg import getstatusoutput
import AbstractCheck
import Config

STANDARD_BIN_DIRS = ['/bin/', '/sbin/', '/usr/bin/', '/usr/sbin/']
DEFAULT_APPDATA_CHECKER = ('appstream-util', 'validate-relax')

appdata_checker = Config.getOption("AppDataChecker", DEFAULT_APPDATA_CHECKER)


class AppDataCheck(AbstractCheck.AbstractFilesCheck):
    def __init__(self):
        # desktop file need to be in $XDG_DATA_DIRS
        # $ echo $XDG_DATA_DIRS/applications
        # /var/lib/menu-xdg:/usr/share
        AbstractCheck.AbstractFilesCheck.__init__(
            self, "AppDataCheck", "/usr/share/appdata/.*\.appdata.xml$")

    def check_file(self, pkg, filename):
        root = pkg.dirName()
        f = root + filename
        try:
            st = getstatusoutput(appdata_checker + (f,))
        except OSError:
            # ignore if the checker is not installed
            return
        if st[0]:
            printError(pkg, 'invalid-appdata-file', filename)


check = AppDataCheck()

addDetails(
'invalid-appdata-file',
'''appdata file is not valid, check with %s''' % (" ".join(appdata_checker)),
)

# Local variables:
# indent-tabs-mode: nil
# py-indent-offset: 4
# End:
# ex: ts=4 sw=4 et
