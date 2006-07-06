# Version         : $Id$

#
# check xdg file format violation
# 
# http://standards.freedesktop.org/desktop-entry-spec/desktop-entry-spec-latest.html
#

from Filter import *
import AbstractCheck
import Config
import subprocess

class MenuXDGCheck(AbstractCheck.AbstractFilesCheck):
    def __init__(self):
        # desktop file need to be in $XDG_DATA_DIRS
        # $ echo $XDG_DATA_DIRS/applications
        # /var/lib/menu-xdg:/usr/share
        AbstractCheck.AbstractFilesCheck.__init__(self, "MenuXDGCheck", "/usr/share/applications/.*\.desktop$")

    def check_file(self, pkg, filename):
        f = open(pkg.dirName() + filename)
        if subprocess.call("desktop-file-validate %s" % f):
                printError(pkg, 'invalid-desktopfile', f)

check=MenuXDGCheck()

if Config.info:
    addDetails(
        'invalid-desktopfile',
        '''.desktop file is not valid, check with desktop-file-validate''',)

