#############################################################################
# File		: ConfigCheck.py
# Package	: rpmlint
# Author	: Frederic Lepied
# Created on	: Sun Oct  3 21:48:20 1999
# Version	: $Id$
# Purpose	: 
#############################################################################

import AbstractCheck
import rpm
import re

class ConfigCheck(AbstractCheck.AbstractCheck):
    games_regex=re.compile("^/var/lib/games")
    usr_regex=re.compile("^/usr/")
    etc_var_regex=re.compile("^/etc/|^/var/")
    appdefaults_regex=re.compile("/app-defaults/")
    
    def __init__(self):
	AbstractCheck.AbstractCheck.__init__(self, "ConfigCheck")

    def check(self, pkg, verbose):
	config_files=pkg.configFiles()
	for c in config_files:
	    if ConfigCheck.appdefaults_regex.search(c):
		print "E:", pkg.name, "app-defaults-must-not-be-conffile", c
	    if ConfigCheck.games_regex.search(c):
		print "E:", pkg.name, "score-file-must-not-be-conffile", c
	    if ConfigCheck.usr_regex.search(c):
		print "E:", pkg.name, "file-in-usr-marked-as-conffile", c
	    elif not ConfigCheck.etc_var_regex.search(c):
		print "W:", pkg.name, "non-etc-or-var-file-marked-as-conffile", c
# Create an object to enable the auto registration of the test
check=ConfigCheck()

# ConfigCheck.py ends here
