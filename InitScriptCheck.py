#---------------------------------------------------------------
# Project         : Linux-Mandrake
# Module          : rpmlint
# File            : InitScriptCheck.py
# Version         : $Id$
# Author          : Frederic Lepied
# Created On      : Fri Aug 25 09:26:37 2000
#---------------------------------------------------------------

from Filter import *
import AbstractCheck
import re
import commands
import rpm

rc_regex=re.compile("^/etc(/rc.d)?/init.d/")
chkconfig_content_regex=re.compile("# chkconfig: +([-0-9]+) +[-0-9]+ +[-0-9]+", re.MULTILINE)
subsys_regex=re.compile("/var/lock/subsys/([^/\n ]+)", re.MULTILINE)
chkconfig_regex=re.compile("^[^#]*chkconfig", re.MULTILINE)
status_regex=re.compile("^[^#]*status", re.MULTILINE)
reload_regex=re.compile("^[^#]*reload", re.MULTILINE)
basename_regex=re.compile("([^/]+)$")

class InitScriptCheck(AbstractCheck.AbstractCheck):

    def __init__(self):
	AbstractCheck.AbstractCheck.__init__(self, "InitScriptCheck")
    
    def check(self, pkg, verbose):
	# Check only binary package
	if pkg.isSource():
	    return

        for f in pkg.files().keys():
            if rc_regex.search(f):
                # check chkconfig call in %post and %preun
                postin=pkg[rpm.RPMTAG_POSTIN] or pkg[rpm.RPMTAG_POSTINPROG]
                if not postin:
                    printError(pkg, "init-script-without-chkconfig-postin", f)
                else:
                    if not chkconfig_regex.search(postin):
                        printError(pkg, "postin-without-chkconfig", f)                    
                    
                preun=pkg[rpm.RPMTAG_PREUN] or pkg[rpm.RPMTAG_PREUNPROG]
                if not preun:
                    printError(pkg, "init-script-without-chkconfig-preun", f)
                else:
                    if not chkconfig_regex.search(preun):
                        printError(pkg, "preun-without-chkconfig", f)

                # check common error in file content
                fd=open(pkg.dirName() + "/" + f, "r")
                content=fd.read(-1)
                fd.close()
                
                if not status_regex.search(content):
                    printError(pkg, "no-status-entry", f)
                    
                if not reload_regex.search(content):
                    printWarning(pkg, "no-reload-entry", f)
                    
                res=chkconfig_content_regex.search(content)
                if not res:
                    printError(pkg, "no-chkconfig-line", f)
                else:
                    if res.group(1) == '-':
                        printWarning(pkg, 'no-default-runlevel')
                        
                res=subsys_regex.search(content)
                if not res:
                    printError(pkg, "subsys-not-used", f)
                else:
                    name=res.group(1)
                    res=basename_regex.search(f)
                    if res:
                        basename=res.group(1)
                        if name != basename:
                            printError(pkg, "incoherent-subsys", f, name)
                    
# Create an object to enable the auto registration of the test
check=InitScriptCheck()

# InitScriptCheck.py ends here
