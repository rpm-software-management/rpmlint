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

def printWarning(pkg, reason, *details):
    _print("W", pkg, reason, details)

def printError(pkg, reason, *details):
    _print("E", pkg, reason, details)

def _print(type, pkg, reason, details):
    if not Config.isFiltered(pkg.name, reason):
	sys.stdout.write("%s: %s %s" % (type, pkg.name, reason))
	for d in details:
	    sys.stdout.write(" %s" % (str(d)))
	sys.stdout.write("\n")

# Filter.py ends here
