# -*- coding: utf-8 -*-
#############################################################################
# File          : Filter.py
# Package       : rpmlint
# Author        : Frederic Lepied
# Created on    : Sat Oct 23 15:52:27 1999
# Purpose       : filter the output of rpmlint to allow exceptions.
#############################################################################

from __future__ import print_function

import locale
import sys
import textwrap

import rpmlint.Config as Config
try:
    import Testing
except ImportError:
    Testing = None


_rawout = None
_diagnostic = list()
_badness_score = 0
printed_messages = {"I": 0, "W": 0, "E": 0}

__preferred_encoding = locale.getpreferredencoding()
if sys.version_info[0] < 3:
    def __print(s):
        if isinstance(s, str):
            s = s.decode(__preferred_encoding, 'replace')
        print(s)
else:
    def __print(s):
        print(s)


def printInfo(pkg, reason, *details):
    _print("I", pkg, reason, details)


def printWarning(pkg, reason, *details):
    _print("W", pkg, reason, details)


def printError(pkg, reason, *details):
    _print("E", pkg, reason, details)


def _print(msgtype, pkg, reason, details):
    global _badness_score

    threshold = badnessThreshold()

    badness = 0
    if threshold >= 0:
        badness = Config.badness(reason)
        # anything with badness is an error
        if badness:
            msgtype = 'E'
        # errors without badness become warnings
        elif msgtype == 'E':
            msgtype = 'W'

    ln = ""
    if pkg.current_linenum is not None:
        ln = "%s:" % pkg.current_linenum
    arch = ""
    if pkg.arch is not None:
        arch = ".%s" % pkg.arch
    s = "%s%s:%s %s: %s" % (pkg.name, arch, ln, msgtype, reason)
    if badness:
        s = s + " (Badness: %d)" % badness
    for d in details:
        s = s + " %s" % d
    if _rawout:
        print(s.encode(locale.getpreferredencoding(), "replace"),
              file=_rawout)
    if not Config.isFiltered(s):
        printed_messages[msgtype] += 1
        _badness_score += badness
        if threshold >= 0:
            _diagnostic.append(s + "\n")
        else:
            __print(s)
            if Config.info:
                printDescriptions(reason)
        return True

    return False


def printDescriptions(reason):
    try:
        d = _details[reason]
        if d and d != '' and d != "\n":
            __print(textwrap.fill(d, 78))
            __print("")
    except KeyError:
        pass


def _diag_sortkey(x):
    xs = x.split()
    return (xs[2], xs[1])


def printAllReasons():
    threshold = badnessThreshold()
    if threshold < 0:
        return False

    global _diagnostic
    _diagnostic.sort(key=_diag_sortkey, reverse=True)
    last_reason = ''
    for diag in _diagnostic:
        if Config.info:
            reason = diag.split()[2]
            if reason != last_reason:
                if len(last_reason):
                    printDescriptions(last_reason)
                last_reason = reason
        __print(diag)
    if Config.info and len(last_reason):
        printDescriptions(last_reason)
    _diagnostic = list()
    return _badness_score > threshold


_details = {}


def addDetails(*details):
    for idx in range(int(len(details) / 2)):
        if not details[idx * 2] in _details:
            _details[details[idx * 2]] = details[idx * 2 + 1]


def badnessScore():
    return _badness_score


def badnessThreshold():
    return Config.getOption("BadnessThreshold", -1)


def setRawOut(file):
    global _rawout
    if _rawout:
        _rawout.close()
    _rawout = open(file, "w")

# Filter.py ends here
