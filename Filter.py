#############################################################################
# File          : Filter.py
# Package       : rpmlint
# Author        : Frederic Lepied
# Created on    : Sat Oct 23 15:52:27 1999
# Version       : $Id$
# Purpose       : filter the output of rpmlint to allow exceptions.
#############################################################################

import sys
import Config
import Testing
try:
    from textwrap import fill # python >= 2.3
except ImportError:
    def fill(text, width=70): return text

printed_messages = { "I": 0, "W": 0, "E": 0 }

def printInfo(pkg, reason, *details):
    if _print("I", pkg, reason, details) and Config.info:
        printDescriptions(reason)

def printWarning(pkg, reason, *details):
    if _print("W", pkg, reason, details) and Config.info:
        printDescriptions(reason)

def printError(pkg, reason, *details):
    if _print("E", pkg, reason, details) and Config.info:
        printDescriptions(reason)

def _print(type, pkg, reason, details):
    ln = ""
    if pkg.current_linenum is not None:
        ln = "%s:" % pkg.current_linenum
    arch = ""
    if pkg.arch is not None:
        arch = ".%s" % pkg.arch
    s = "%s%s:%s %s: %s" % (pkg.name, arch, ln, type, reason)
    for d in details:
        s = s + " %s" % d
    if Testing.isTest():
        Testing.addOutput(s)
    else:
        if not Config.isFiltered(s):
            printed_messages[type] = printed_messages[type] + 1
            sys.stdout.write(s)
            sys.stdout.write("\n")
            return 1

    return 0

def printDescriptions(reason):
    try:
        d = _details[reason]
        if d and d != '' and d != "\n":
            sys.stdout.write(fill(d, 78))
            sys.stdout.write("\n\n")
    except KeyError:
        pass

_details={}

def addDetails(*details):
    for idx in range(len(details)/2):
        _details[details[idx*2]]=details[idx*2+1]

# Filter.py ends here

# Local variables:
# indent-tabs-mode: nil
# py-indent-offset: 4
# End:
# ex: ts=4 sw=4 et
