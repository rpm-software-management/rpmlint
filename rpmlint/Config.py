# -*- coding: utf-8 -*-
#############################################################################
# File          : Config.py
# Package       : rpmlint
# Author        : Frederic Lepied
# Created on    : Fri Oct 15 20:04:25 1999
# Purpose       : handle configuration options. To be used from config files.
#############################################################################

import locale
import os.path
import re

try:
    import __version__
except ImportError:
    __version__ = 'devel'

DEFAULT_CHECKS = ("DistributionCheck",
                  "TagsCheck",
                  "BinariesCheck",
                  "ConfigCheck",
                  "FilesCheck",
                  "DocFilesCheck",
                  "FHSCheck",
                  "SignatureCheck",
                  "I18NCheck",
                  "MenuCheck",
                  "PostCheck",
                  "InitScriptCheck",
                  "SourceCheck",
                  "SpecCheck",
                  "NamingPolicyCheck",
                  "ZipCheck",
                  "PamCheck",
                  "RpmFileCheck",
                  "MenuXDGCheck",
                  "AppDataCheck",
                  )

USEUTF8_DEFAULT = False
try:
    if locale.getpreferredencoding() == 'UTF-8':
        USEUTF8_DEFAULT = True
except UnicodeError:
    try:
        if re.match('utf', locale.getdefaultlocale()[1], re.I):
            USEUTF8_DEFAULT = True
    except UnicodeError:
        pass

info = False
no_exception = False

# handle the list of checks to load
_checks = []
_checks.extend(DEFAULT_CHECKS)


def addCheck(check):
    check = re.sub(r'\.py[co]?$', '', check)
    if check not in _checks:
        _checks.append(check)


def allChecks():
    if _checks == []:
        defaultChecks()
    return _checks


def defaultChecks():
    resetChecks()
    _checks.extend(DEFAULT_CHECKS)


def resetChecks():
    global _checks

    _checks = []


# handle the list of directories to look for checks

_dirs = ["/usr/share/rpmlint"]


def addCheckDir(dir):
    d = os.path.expanduser(dir)
    if d not in _dirs:
        _dirs.insert(0, d)


def checkDirs():
    return _dirs


# handle options

_options = {}


def setOption(name, value):
    _options[name] = value


def getOption(name, default=""):
    return _options.get(name, default)


# List of filters
_filters = []
_filters_re = None


def addFilter(s):
    global _filters_re

    _filters.append(s)
    _filters_re = None


def removeFilter(s):
    global _filters_re

    try:
        _filters.remove(s)
    except ValueError:
        pass
    else:
        _filters_re = None


_scoring = {}


def setBadness(s, score):
    _scoring[s] = score


def badness(s):
    return _scoring.get(s, 0)


_non_named_group_re = re.compile(r'[^\\](\()[^:]')


def isFiltered(s):
    global _filters_re

    if _filters_re is None:
        # no filter
        if len(_filters) == 0:
            return False
        _filters_re = '(?:' + _filters[0] + ')'

        for idx in range(1, len(_filters)):
            # to prevent named group overflow that happen when there is too
            # many () in a single regexp: AssertionError: sorry, but this
            # version only supports 100 named groups
            if '(' in _filters[idx]:
                _non_named_group_re.subn('(:?', _filters[idx])
            _filters_re = _filters_re + '|(?:' + _filters[idx] + ')'
        _filters_re = re.compile(_filters_re)

    if not no_exception:
        if _filters_re.search(s):
            return True
    return False

# Config.py ends here
