#############################################################################
# File		: Config.py
# Package	: rpmlint
# Author	: Frederic Lepied
# Created on	: Fri Oct 15 20:04:25 1999
# Version	: $Id$
# Purpose	: handle configuration options. To be used from config files.
#############################################################################

import os.path
import re

DEFAULT_CHECKS=("DistributionCheck",
		"TagsCheck",
		"BinariesCheck",
		"ConfigCheck",
		"FilesCheck",
#		"FHSCheck",
		"SignatureCheck",
                "MenuCheck",
                "PostCheck",
		"SourceCheck")

# handle the list of checks to load
_checks=[]

def addCheck(check):
    global _checks
    
    if not check in _checks:
	_checks.append(check)

def allChecks():
    global _checks
    
    if _checks == []:
	_checks=DEFAULT_CHECKS
    return _checks

def defaultChecks():
    global _checks

    _checks=DEFAULT_CHECKS
    
def resetChecks():
    global _checks

    _checks=[]
    
# handle the list of directories to look for checks

_dirs=["/usr/share/rpmlint"]

def addCheckDir(dir):
    global _dirs

    dir=os.path.expanduser(dir)
    
    if not dir in _dirs:
	_dirs.insert(0, dir)

def checkDirs():
    global _dirs

    return _dirs

# handle options

_options={}

def setOption(name, value):
    global _options

    _options[name]=value

def getOption(name, default):
    global _options
    
    try:
	return _options[name]
    except KeyError:
	return default

# List of filters
_filters=[]

def addFilter(s):
    global _filters

    _filters.append(re.compile(s))

def isFiltered(s):
    global _filters

    for f in _filters:
	if f.search(s):
	    return 1
    return 0
    
# Config.py ends here
