#!/usr/bin/env python
#---------------------------------------------------------------
# Project         : Linux-Mandrake
# Module          : rpmlint
# File            : check-install
# Version         : $Id$
# Author          : Frederic Lepied
# Created On      : Fri Oct 13 20:40:08 2000
#---------------------------------------------------------------

import rpm
import Pkg

db=rpm.opendb()
idx=db.firstkey()

while idx:
    pkg=Pkg.Pkg(None, None, db[idx])
    for (dep,ver,flags) in pkg.requires() + pkg.prereq():
        if dep != 'rpmlib(VersionedDependencies)' and not db.findbyname(dep) and not db.findbyprovides(dep) and not db.findbyfile(dep):
            print 'unsatisfied dependency', dep, 'for', pkg.name
    idx=db.nextkey(idx)

del db

# check-install ends here
