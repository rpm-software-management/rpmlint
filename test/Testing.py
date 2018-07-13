# -*- coding: utf-8 -*-

import glob
import os
import tempfile

from rpmlint.Pkg import FakePkg, Pkg


def _testpath():
    return os.environ.get(
        'TESTPATH',
        os.path.dirname(__file__)
    )


TEST_CONFIG = os.path.join(_testpath(), "test.config")
with open(TEST_CONFIG) as f:
    exec(compile(f.read(), TEST_CONFIG, 'exec'))


def getTestedPath(path):
    return os.path.join(_testpath(), path)


def getTestedPackage(name):
    pkg_path = glob.glob(getTestedPath(name) + "-*.rpm")[0]
    return Pkg(pkg_path, tempfile.gettempdir())


def getTestedSpecPackage(name):
    pkg_path = glob.glob(getTestedPath(name) + ".spec")[0]
    return FakePkg(pkg_path)
