#############################################################################
# File          : Config.py
# Package       : rpmlint
# Author        : Frederic Lepied
# Created on    : Fri Oct 15 20:04:25 1999
# Version       : $Id$
# Purpose       : handle configuration options. To be used from config files.
#############################################################################

import os.path
import re
from setuplist import *

DEFAULT_CHECKS=("DistributionCheck",
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
                )

USEUTF8_DEFAULT=0
try:
    from locale import getpreferredencoding
    if getpreferredencoding() == 'UTF-8': USEUTF8_DEFAULT=1
except:
    try:
        from locale import getdefaultlocale
        if re.match('utf', getdefaultlocale()[1], re.I): USEUTF8_DEFAULT=1
    except:
        pass

info=0
no_exception=0

# handle the list of checks to load
_checks=[]

def addCheck(check):
    global _checks

    if not check in _checks:
        _checks.append(check)

def allChecks():
    global _checks

    if _checks == []:
        defaultChecks()
    return _checks

def defaultChecks():
    resetChecks()
    _checks.extend(DEFAULT_CHECKS)

def resetChecks():
    global _checks

    _checks=[]

# handle the list of directories to look for checks

_dirs=["/usr/share/rpmlint"]

def addCheckDir(dir):
    global _dirs

    d = os.path.expanduser(dir)

    if not d in _dirs:
        _dirs.insert(0, d)

def checkDirs():
    global _dirs

    return _dirs

# handle options

_options={}

def setOption(name, value):
    global _options

    _options[name]=value

def getOption(name, default=""):
    global _options

    try:
        return _options[name]
    except:
        return default

# List of filters
_filters=[]
_filters_re=None

def addFilter(s):
    global _filters
    global _filters_re

    _filters.append(s)
    _filters_re=None

_non_named_group_re = re.compile('[^\\](\()[^:]')
def isFiltered(s):
    global _filters
    global _filters_re

    if _filters_re == None:
        # no filter
        if len(_filters) == 0:
            return 0
        _filters_re = '(?:' + _filters[0] + ')'

        for idx in range(1, len(_filters)):
            # to prevent named group overflow that happen when there is too many () in a single regexp
            # AssertionError: sorry, but this version only supports 100 named groups
            if _filters[idx].find('(') > -1:
                _non_named_group_re.subn('(:?', _filters[idx])
            _filters_re = _filters_re + '|(?:' + _filters[idx] +')'
        _filters_re = re.compile(_filters_re)

    if not no_exception:
        if _filters_re.search(s):
            return 1
    return 0

# Config.py ends here

# Local variables:
# indent-tabs-mode: nil
# py-indent-offset: 4
# End:
# ex: ts=4 sw=4 et
