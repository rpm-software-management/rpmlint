# -*- coding: utf-8 -*-

import glob
import os
import tempfile

import Pkg


TEST_CONFIG = os.path.join(os.environ['TESTPATH'], 'test.config')
exec(compile(open(TEST_CONFIG).read(), TEST_CONFIG, 'exec'))

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

# ex: ts=4 sw=4 et
