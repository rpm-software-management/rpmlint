#############################################################################
# File		: ScriptCheck.py
# Package	: rpmlint
# Author	: Chmouel Boudjnah
# Created on	: Thu Jul 27 19:00:17 PDT 2000
# Version	: $Id$
# Purpose	: test various aspects on scripts
#############################################################################

from Filter import *
import AbstractCheck
import rpm
import os

def check_shell_script(self):
    tmpfile = "/tmp/.bash-script.%d" % os.getpid()
    if not self:
        return 0
    script = open(tmpfile, 'w')
    script.write(self)
    script.close
    os.system("/bin/bash -n %s " % tmpfile)
    if os.error:
        os.remove(tmpfile)
        return 1
    os.remove(tmpfile)

class ScriptCheck(AbstractCheck.AbstractCheck):
    
    def __init__(self):
        AbstractCheck.AbstractCheck.__init__(self, "ScriptCheck")

    def check(self, pkg, verbose):

        if pkg.isSource():
            return

        for tag in ((rpm.RPMTAG_PREIN, "%pre"), (rpm.RPMTAG_POSTIN, "%post"),
                    (rpm.RPMTAG_PREUN, "%preun"), (rpm.RPMTAG_POSTUN, "%postun")):
            script=pkg[tag[0]]
            if script and check_shell_script(script):
                printError(pkg, "shell-syntax-error-in " + tag[1])

check=ScriptCheck()
