#############################################################################
# File          : FHSCheck.py
# Package       : rpmlint
# Author        : Frederic Lepied
# Created on    : Fri Oct 15 17:40:32 1999
# Version       : $Id$
# Purpose       : check FHS conformity
#############################################################################

from Filter import *
import AbstractCheck
import re

class FHSCheck(AbstractCheck.AbstractCheck):
    usr_regex=re.compile("^/usr/([^/]+)/")
    usr_subdir = ('X11R6','X386','bin','games','include','lib','lib64','local','sbin','share','src','spool','tmp')
    var_regex=re.compile("^/var/([^/]+)/")
    var_fsstnd = ('adm','catman','local','named','nis','preserve')
    var_subdir = ('account','lib','cache','crash','games','lock','log','opt','run','spool','state','tmp','yp','www','ftp')

    def __init__(self):
        AbstractCheck.AbstractCheck.__init__(self, "FHSCheck")

    def check(self, pkg):
        # Check only binary package
        if pkg.isSource():
            return

        files=pkg.files()
        var_list=[]
        usr_list=[]

        for f in files.keys():
            s=FHSCheck.usr_regex.search(f)
            if s:
                d = s.group(1)
                if not d in FHSCheck.usr_subdir:
                    if not d in usr_list:
                        printWarning(pkg, "non-standard-dir-in-usr", d)
                        usr_list.append(d)
            else:
                s=FHSCheck.var_regex.search(f)
                if s:
                    d = s.group(1)
                    if d in FHSCheck.var_fsstnd:
                        if not d in var_list:
                            printWarning(pkg, "FSSTND-dir-in-var", f)
                            var_list.append(d)
                    elif not d in FHSCheck.var_subdir:
                        if not d in var_list:
                            printWarning(pkg, "non-standard-dir-in-var", d)
                            var_list.append(d)

# Create an object to enable the auto registration of the test
check=FHSCheck()

if Config.info:
    addDetails(
'non-standard-dir-in-usr',
"""Your package is creating a non-standard subdirectory in /usr. The standard
directories are:
        -X11R6          -X386
        -bin            -games
        -include        -lib
        -local          -sbin
        -share          -src
        -spool          -tmp
        -lib64
""",

'FSSTND-dir-in-var',
"""Your package is creating an illegal directory in /var. The FSSTND (illegal)
ones are:
        -adm            -catman
        -local          -named
        -nis            -preserve
""",

'non-standard-dir-in-var',
"""Your package is creating a non-standard subdirectory in /var. The standard
directories are:
        -account        -lib
        -cache          -crash
        -games          -lock
        -log            -opt
        -run            -spool
        -state          -tmp
        -yp             -www
        -ftp
""",
)

# FHSCheck.py ends here

# Local variables:
# indent-tabs-mode: nil
# py-indent-offset: 4
# End:
# ex: ts=4 sw=4 et
