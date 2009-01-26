# -*- coding: utf-8 -*-

import glob
import os
import tempfile

import Pkg


currently_testing = 0
output = []

def isTest():
    return currently_testing

def startTest():
    global currently_testing
    global output
    output = []
    currently_testing = 1

def addOutput(s):
    global output
    output.append(s)

def getOutput():
    global output
    return output

def getTestedPackage(name):
    pkg_path = glob.glob(os.environ['TESTPATH'] + '/' + name + '-*.rpm')[0]
    return Pkg.Pkg(pkg_path, tempfile.gettempdir())

def getTestedSpecPackage(name):
    pkg_path = glob.glob(os.environ['TESTPATH'] + '/' + name + '.spec')[0]
    return Pkg.FakePkg(pkg_path)

# Local variables:
# indent-tabs-mode: nil
# py-indent-offset: 4
# End:
# ex: ts=4 sw=4 et
