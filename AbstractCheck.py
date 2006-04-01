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

# AbstractCheck.py ends here

# Local variables:
# indent-tabs-mode: nil
# py-indent-offset: 4
# End:
# ex: ts=4 sw=4 et
