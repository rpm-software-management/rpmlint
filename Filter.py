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

def printWarning(pkg, reason, *details):
    _print("W", pkg, reason, details)

def printError(pkg, reason, *details):
    _print("E", pkg, reason, details)

def _print(type, pkg, reason, details):
    s="%s: %s %s" % (type, pkg.name, reason)
    for d in details:
	s = s + " %s" % d
    
    if not Config.isFiltered(s):
	sys.stdout.write(s)
	sys.stdout.write("\n")

# Filter.py ends here
