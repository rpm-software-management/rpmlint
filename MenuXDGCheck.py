# Version         : $Id$

#
# check xdg file format violation
#

from Filter import *
import AbstractCheck
import Config
import subprocess

class MenuXDGCheck(AbstractCheck.AbstractFilesCheck):
    def __init__(self):
        AbstractCheck.AbstractFilesCheck.__init__(self, "MenuXDGCheck", ".*\.desktop$")

    def check_file(self, pkg, filename):
        f = open(pkg.dirName() + filename)
        if subprocess.call("desktop-file-validate %s" % f):
                printError(pkg, 'invalid-desktopfile', f)

check=MenuXDGCheck()

if Config.info:
    addDetails(
        'invalid-desktopfile',
        '''.desktop file is not valid, check with desktop-file-validate''',)

