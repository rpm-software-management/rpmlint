#!/usr/bin/python -O -tt
#############################################################################
# File          : compile.py
# Package       : rpmlint
# Author        : Frederic Lepied
# Created on    : Sat Oct 23 23:40:21 1999
# Version       : $Id$
# Purpose       : byte compile all python files given in arguments.
#############################################################################

import py_compile
import sys

for f in sys.argv[2:]:
    py_compile.compile(f, f + 'o', sys.argv[1] + f)

# compile.py ends here

# Local variables:
# indent-tabs-mode: nil
# py-indent-offset: 4
# End:
# ex: ts=4 sw=4 et
