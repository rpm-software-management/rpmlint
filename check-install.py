#!/usr/bin/env python
#---------------------------------------------------------------
# Project         : Mandrakelinux
# Module          : rpmlint
# File            : check-install.py
# Version         : $Id$
# Author          : Frederic Lepied
# Created On      : Fri Oct 13 20:40:08 2000
#---------------------------------------------------------------

import rpm
import Pkg

db=rpm.opendb()
idx=db.firstkey()

def check_name(db, name):
    try:
        return db.findbyname(name)
    except:
        return None
    
def check_provides(db, name):
    if name[0:7] == 'rpmlib(':
        return 1
    try:
        return db.findbyprovides(name)
    except:
        return None
    
def check_file(db, name):
    try:
        return db.findbyfile(name)
    except:
        return None
    
while idx:
    pkg=Pkg.Pkg(None, None, db[idx])
    for (dep,ver,flags) in pkg.requires() + pkg.prereq():
        if  not check_name(db, dep) and not check_provides(db, dep) and not check_file(db, dep):
            print 'unsatisfied dependency', dep, 'for', pkg.name
    idx=db.nextkey(idx)

del db

# check-install ends here
