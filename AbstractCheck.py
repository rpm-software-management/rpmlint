# -*- coding: utf-8 -*-
#############################################################################
# File          : AbstractCheck.py
# Package       : rpmlint
# Author        : Frederic Lepied
# Created on    : Tue Sep 28 00:22:38 1999
# Version       : $Id$
# Purpose       : Abstract class to hold all the derived classes.
#############################################################################

import re


# Note: do not add any capturing parentheses here
macro_regex = re.compile('%+[{(]?\w+[)}]?')

class AbstractCheck:
    known_checks = {}

    def __init__(self, name):
        if not AbstractCheck.known_checks.get(name):
            AbstractCheck.known_checks[name] = self
        self.name = name
        self.verbose = False

    def check(self, pkg):
        raise NotImplementedError('check must be implemented in subclass')


class AbstractFilesCheck(AbstractCheck):
    def __init__(self, name, file_regexp):
        self.__files_re = re.compile(file_regexp)
        AbstractCheck.__init__(self, name)
    def check(self, pkg):
        if pkg.isSource():
            return
        for filename in pkg.files():
            if self.__files_re.match(filename):
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
