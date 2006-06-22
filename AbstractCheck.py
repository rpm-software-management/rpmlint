#############################################################################
# File          : AbstractCheck.py
# Package       : rpmlint
# Author        : Frederic Lepied
# Created on    : Tue Sep 28 00:22:38 1999
# Version       : $Id$
# Purpose       : Abstract class to hold all the derived classes.
#############################################################################

class AbstractCheck:
    checks=[]

    def __init__(self, name):
        AbstractCheck.checks.append(self)
        self.name = name

    def check(self, pkg):
        raise NotImplementedError('check must be implemented in subclass')


import re

class AbstractFilesCheck(AbstractCheck):
    def __init__(self, name, file_regexp):
        self.__files_re = re.compile(file_regexp)
        AbstractCheck.__init__(self, name)
    def check(self, pkg):
        if pkg.isSource():
            return
        files = []
        for f in pkg.files().keys():
            if self.__files_re.match(f):
                files.append(f)
        for i in files:
            self.check_file(pkg, i)

 
    def check_file(self, pkg, file):
        """ Virtual method called for each file that match the regexp passed to the constructor """
        raise NotImplementedError('check must be implemented in subclass')
        
# AbstractCheck.py ends here

# Local variables:
# indent-tabs-mode: nil
# py-indent-offset: 4
# End:
# ex: ts=4 sw=4 et
