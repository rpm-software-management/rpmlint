# -*- coding: utf-8 -*-

import glob
import os
import tempfile

import Pkg


def _testpath():
    return os.environ.get(
        'TESTPATH',
        os.path.join(os.path.dirname(__file__), "..", "test")
    )


TEST_CONFIG = os.path.join(_testpath(), "test.config")
with open(TEST_CONFIG) as f:
    exec(compile(f.read(), TEST_CONFIG, 'exec'))

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
    pkg_path = glob.glob(os.path.join(_testpath(), name) + "-*.rpm")[0]
    return Pkg.Pkg(pkg_path, tempfile.gettempdir())


def getTestedSpecPackage(name):
    pkg_path = glob.glob(os.path.join(_testpath(), name) + ".spec")[0]
    return Pkg.FakePkg(pkg_path)

# ex: ts=4 sw=4 et
