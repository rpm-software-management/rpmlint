#############################################################################
# File		: ConfigCheck.py
# Package	: rpmlint
# Author	: Frederic Lepied
# Created on	: Sun Oct  3 21:48:20 1999
# Version	: $Id$
# Purpose	: 
#############################################################################

from Filter import *
import AbstractCheck
import rpm
import re

class ConfigCheck(AbstractCheck.AbstractCheck):
    games_regex=re.compile("^/var/lib/games")
    usr_regex=re.compile("^/usr/")
    etc_var_regex=re.compile("^/etc/|^/var/")
    appdefaults_regex=re.compile("^/usr/X11R6/lib/X11/app-defaults/")
    
    def __init__(self):
	AbstractCheck.AbstractCheck.__init__(self, "ConfigCheck")

    def check(self, pkg, verbose):
	# Check only binary package
	if pkg.isSource():
	    return
	
	config_files=pkg.configFiles()
        noreplace_files=pkg.noreplaceFiles()
        
	for c in config_files:
	    if ConfigCheck.appdefaults_regex.search(c):
		printError(pkg, "app-defaults-must-not-be-conffile", c)
	    if ConfigCheck.games_regex.search(c):
		printError(pkg, "score-file-must-not-be-conffile", c)
	    if ConfigCheck.usr_regex.search(c):
		printError(pkg, "file-in-usr-marked-as-conffile", c)
	    elif not ConfigCheck.etc_var_regex.search(c):
		printWarning(pkg, "non-etc-or-var-file-marked-as-conffile", c)

            if not c in noreplace_files:
                printWarning(pkg, "conffile-without-noreplace-flag", c)
                
# Create an object to enable the auto registration of the test
check=ConfigCheck()

# Add information about checks
if Config.info:
    addDetails(
'app-defaults-must-not-be-conffile',
"""A file in /usr/X11R6/lib/X11/app-defaults/ is a configuration file.
If you need to store your conf file, put it in /etc.""",

'score-file-must-not-be-conffile',
"""A file in /var/lib/games/ is a configuration file. Store your conf
files in /etc instead.""",

'file-in-usr-marked-as-conffile',
"""A file in /usr is marked as being a configuration file.
Store your conf files in /etc/ instead.""",

'non-etc-or-var-file-marked-as-conffile',
"""A file not in /etc or /var is marked as being a configuration file.
Please put your conf files in /etc or /var.""",

'conffile-without-noreplace-flag',
"""A configuration file is stored in your package without the noreplace flag.
A way to resolve this is to put the following in your SPEC file:

%config(noreplace) /etc/your_config_file_here
""",

)

# ConfigCheck.py ends here
