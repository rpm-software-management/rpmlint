#############################################################################
# File          : AbstractCheck.py
# Package       : rpmlint
# Author        : Frederic Lepied
# Created on    : Tue Sep 28 00:22:38 1999
# Version       : $Id$
# Purpose       : Abstract class to hold all the derived classes.
#############################################################################

class AbstractCheck:
    check_names_seen = []
    checks = []

    def __init__(self, name):
        if name not in AbstractCheck.check_names_seen:
            AbstractCheck.checks.append(self)
            AbstractCheck.check_names_seen.append(name)
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
        for filename in pkg.files().keys():
            if self.__files_re.match(filename):
                files.append(filename)
        for filename in files:
            self.check_file(pkg, filename)

 
    def check_file(self, pkg, filename):
        """Virtual method called for each file that match the regexp passed
        to the constructor.
        """
        raise NotImplementedError('check must be implemented in subclass')
        
# AbstractCheck.py ends here

# Local variables:
# indent-tabs-mode: nil
# py-indent-offset: 4
# End:
# ex: ts=4 sw=4 et
