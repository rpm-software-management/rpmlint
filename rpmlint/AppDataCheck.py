# -*- coding: utf-8 -*-

#
# check appdata file format violation
#
# http://people.freedesktop.org/~hughsient/appdata/
#

import xml.etree.ElementTree as ET

import rpmlint.AbstractCheck as AbstractCheck
import rpmlint.Config as Config
from rpmlint.Filter import addDetails, printError
from rpmlint.Pkg import getstatusoutput

STANDARD_BIN_DIRS = ['/bin/', '/sbin/', '/usr/bin/', '/usr/sbin/']
DEFAULT_APPDATA_CHECKER = ('appstream-util', 'validate-relax')

appdata_checker = Config.getOption("AppDataChecker", DEFAULT_APPDATA_CHECKER)


class AppDataCheck(AbstractCheck.AbstractFilesCheck):
    def __init__(self):
        # desktop file need to be in $XDG_DATA_DIRS
        # $ echo $XDG_DATA_DIRS/applications
        # /var/lib/menu-xdg:/usr/share
        AbstractCheck.AbstractFilesCheck.__init__(
            self, "AppDataCheck", r"/usr/share/appdata/.*\.appdata.xml$")

    def check_file(self, pkg, filename):
        root = pkg.dirName()
        f = root + filename

        checker = appdata_checker
        if checker[0] == "appstream-util" and not self.network_enabled:
            checker += ("--nonet",)
        validation_failed = False
        try:
            st = getstatusoutput(checker + (f,))
            # Return code nonzero?
            validation_failed = (st[0] != 0)
        except OSError:
            # checker is not installed, do a validation manually
            try:
                ET.parse(pkg.dirName() + filename)
            except ET.ParseError:
                validation_failed = True
        if validation_failed:
            printError(pkg, 'invalid-appdata-file', filename)


check = AppDataCheck()

addDetails(
'invalid-appdata-file',
'''appdata file is not valid, check with %s''' % (" ".join(appdata_checker)),
)
