#############################################################################
# File		: Filter.py
# Package	: rpmlint
# Author	: Frederic Lepied
# Created on	: Sat Oct 23 15:52:27 1999
# Version	: $Id$
# Purpose	: filter the output of rpmlint to allow exceptions.
#############################################################################

import sys
import Config

def printInfo(pkg, reason, *details):
    _print("I", pkg, reason, details)
    if Config.info:
        printDescriptions(reason)
        
def printWarning(pkg, reason, *details):
    _print("W", pkg, reason, details)
    if Config.info:
        printDescriptions(reason)

def printError(pkg, reason, *details):
    _print("E", pkg, reason, details)
    if Config.info:
        printDescriptions(reason)

def _print(type, pkg, reason, details):
    s="%s: %s %s" % (type, pkg.name, reason)
    for d in details:
	s = s + " %s" % d
    
    if not Config.isFiltered(s):
	sys.stdout.write(s)
	sys.stdout.write("\n")

def printDescriptions(reason):
    try:
        d = _details[reason]
        if d and d != '' and d != "\n":
            sys.stdout.write(d)
            sys.stdout.write("\n\n")
    except KeyError:
        pass
    
_details={}

def addDetails(*details):
    for idx in range(len(details)/2):
        _details[details[idx*2]]=details[idx*2+1]
    
# Filter.py ends here
