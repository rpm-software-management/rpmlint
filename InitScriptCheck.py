#---------------------------------------------------------------
# Project         : Mandriva Linux
# Module          : rpmlint
# File            : InitScriptCheck.py
# Version         : $Id$
# Author          : Frederic Lepied
# Created On      : Fri Aug 25 09:26:37 2000
# Purpose         : check init scripts (files in /etc/rc.d/init.d)
#---------------------------------------------------------------

from Filter import *
import AbstractCheck
import re
import rpm
import Pkg
import string

rc_regex=re.compile('^/etc(/rc.d)?/init.d/')
chkconfig_content_regex=re.compile('# +chkconfig: +([-0-9]+) +[-0-9]+ +[-0-9]+', re.MULTILINE)
subsys_regex=re.compile('/var/lock/subsys/([^/"\'\n ]+)', re.MULTILINE)
chkconfig_regex=re.compile('^[^#]*(chkconfig|add-service|del-service)', re.MULTILINE)
status_regex=re.compile('^[^#]*status', re.MULTILINE)
reload_regex=re.compile('^[^#]*reload', re.MULTILINE)
basename_regex=re.compile('([^/]+)$')
dot_in_name_regex=re.compile('.*\..*')

class InitScriptCheck(AbstractCheck.AbstractCheck):

    def __init__(self):
	AbstractCheck.AbstractCheck.__init__(self, 'InitScriptCheck')
    
    def check(self, pkg):
	# Check only binary package
	if pkg.isSource():
	    return

        list=[]
        for f in pkg.files().keys():
            if rc_regex.search(f):
                basename=basename_regex.search(f).group(1)
                list.append(basename)
		if pkg.files()[f][0] & 0500 != 0500:
		    printError(pkg, 'init-script-non-executable',f)
	    
		if dot_in_name_regex.match(basename):
			printError(pkg, 'init-script-name-with-dot', f)
                # check chkconfig call in %post and %preun
                postin=pkg[rpm.RPMTAG_POSTIN] or pkg[rpm.RPMTAG_POSTINPROG]
                if not postin:
                    printError(pkg, 'init-script-without-chkconfig-postin', f)
                else:
                    if not chkconfig_regex.search(postin):
                        printError(pkg, 'postin-without-chkconfig', f)                    
                    
                preun=pkg[rpm.RPMTAG_PREUN] or pkg[rpm.RPMTAG_PREUNPROG]
                if not preun:
                    printError(pkg, 'init-script-without-chkconfig-preun', f)
                else:
                    if not chkconfig_regex.search(preun):
                        printError(pkg, 'preun-without-chkconfig', f)

                # check common error in file content
                fd=open(pkg.dirName() + '/' + f, 'r')
                content=fd.read(-1)
                fd.close()
                
                if not status_regex.search(content):
                    printError(pkg, 'no-status-entry', f)
                    
                if not reload_regex.search(content):
                    printWarning(pkg, 'no-reload-entry', f)
                    
                res=chkconfig_content_regex.search(content)
                if not res:
                    printError(pkg, 'no-chkconfig-line', f)
                else:
                    if res.group(1) == '-':
                        printWarning(pkg, 'no-default-runlevel')
                        
                res=subsys_regex.search(content)
                if not res:
                    printError(pkg, 'subsys-not-used', f)
                else:
                    name=res.group(1)
                    if name != basename:
                        error=1
                        if name[0] == '$':
                            value=Pkg.substitute_shell_vars(name, content)
                            # If value still starts with '$', substitution has
                            # failed probably due to a more complex shell
                            # expression than what we can handle; don't blame
                            # the package for that.
                            if value == basename or value[0] == '$':
                                error=0
                        if error:
                            printError(pkg, 'incoherent-subsys', f, name)

        if len(list) == 1 and string.lower(pkg[rpm.RPMTAG_NAME]) != list[0]:
            printWarning(pkg, 'incoherent-init-script-name', list[0])
	    
                
# Create an object to enable the auto registration of the test
check=InitScriptCheck()

if Config.info:
    addDetails(
'init-script-without-chkconfig-postin',
'''The package contains an init script but doesn't contain a %post with
a call to chkconfig.''',

'postin-without-chkconfig',
'''The package contains an init script but doesn't call chkconfig in its %post.''',

'init-script-without-chkconfig-preun',
'''The package contains an init script but doesn't contain a %preun with
a call to chkconfig.''',

'preun-without-chkconfig',
'''The package contains an init script but doesn't call chkconfig in its %preun.''',

'no-status-entry',
'''In your init script (/etc/rc.d/init.d/your_file), you don't
have a 'status' entry, which is necessary for good functionality.''',

'no-reload-entry',
'''In your init script (/etc/rc.d/init.d/your_file), you don't
have a 'reload' entry, which is necessary for good functionality.''',

'no-chkconfig-line',
'''The init script doesn't contain a chkconfig line to specify the runlevels
at which to start and stop it.''',

'no-default-runlevel',
'''The default runlevel isn't specified in the init script.''',

'subsys-not-used',
'''While your daemon is running, you have to put a lock file in
/var/lock/subsys/. To see an example, look at this directory on your
machine and examine the corresponding init scripts.''',

'incoherent-subsys',
'''The filename of your lock file in /var/lock/subsys/ is incoherent
with your actual init script name. For example, if your script name
is httpd, you have to use 'httpd' as the filename in your subsys directory.''',

'incoherent-init-script-name',
'''The init script name should be the same as the package name in lower case.''',

'init-script-name-with-dot',
'''The init script name should not contain a dot in its name. Some versions
of chkconfig don't work as expected with init script names like that.''',

'init-script-non-executable',
'''The init script should have at least the execution bit set for root
in order for it to run at boot time.''',
)
# InitScriptCheck.py ends here
