# -*- coding: utf-8 -*-
#############################################################################
# File          : FHSCheck.py
# Package       : rpmlint
# Author        : Frederic Lepied
# Created on    : Fri Oct 15 17:40:32 1999
# Purpose       : check FHS conformity
#############################################################################

import re

import rpmlint.AbstractCheck as AbstractCheck
from rpmlint.Filter import addDetails, printWarning


class FHSCheck(AbstractCheck.AbstractCheck):
    usr_regex = re.compile("^/usr/([^/]+)/")
    usr_subdir = ('X11R6', 'bin', 'games', 'include', 'lib', 'lib64',
                  'local', 'sbin', 'share', 'src', 'tmp')
    var_regex = re.compile("^/var/([^/]+)/")
    var_fsstnd = ('adm', 'catman', 'local', 'named', 'nis', 'preserve')
    var_subdir = ('account', 'cache', 'crash', 'games', 'lib', 'lock', 'log',
                  'mail', 'opt', 'run', 'spool', 'tmp', 'yp', 'www', 'ftp')

    def __init__(self):
        AbstractCheck.AbstractCheck.__init__(self, "FHSCheck")

    def check_binary(self, pkg):
        var_list = []
        usr_list = []

        for fname in pkg.files():
            s = FHSCheck.usr_regex.search(fname)
            if s:
                d = s.group(1)
                if d not in FHSCheck.usr_subdir and d not in usr_list:
                    printWarning(pkg, "non-standard-dir-in-usr", d)
                    usr_list.append(d)
            else:
                s = FHSCheck.var_regex.search(fname)
                if s:
                    d = s.group(1)
                    if d in var_list:
                        continue
                    if d in FHSCheck.var_fsstnd:
                        printWarning(pkg, "FSSTND-dir-in-var", fname)
                        var_list.append(d)
                    elif d not in FHSCheck.var_subdir:
                        printWarning(pkg, "non-standard-dir-in-var", d)
                        var_list.append(d)


# Create an object to enable the auto registration of the test
check = FHSCheck()

addDetails(
'non-standard-dir-in-usr',
"""Your package is creating a non-standard subdirectory in /usr. The standard
directories are:
%s.""" % ", ".join(FHSCheck.usr_subdir),

'FSSTND-dir-in-var',
"""Your package is creating an illegal directory in /var. The FSSTND (illegal)
ones are:
%s.""" % ", ".join(FHSCheck.var_fsstnd),

'non-standard-dir-in-var',
"""Your package is creating a non-standard subdirectory in /var. The standard
directories are:
%s.""" % ", ".join(FHSCheck.var_subdir),
)

# FHSCheck.py ends here
