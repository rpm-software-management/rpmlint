#############################################################################
# File		: Config.py
# Package	: rpmlint
# Author	: Frederic Lepied
# Created on	: Fri Oct 15 20:04:25 1999
# Version	: $Id$
# Purpose	: handle configuration options. To be used from config files.
#############################################################################

import os.path

DEFAULT_CHECKS=("MandrakeCheck",
		"TagsCheck",
		"BinariesCheck",
		"ConfigCheck",
		"FilesCheck",
		"FHSCheck",
		"SignatureCheck")

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
_filters={}

def addFilter(name, reason):
    global _filters

    try:
	_filters[name].append(reason)
    except KeyError:
	_filters[name]=[reason,]

def isFiltered(name, reason):
    global _filters
    
    try:
	reasons=_filters[name]
	return reason in reasons
    except KeyError:
	return 0
    
# Config.py ends here
