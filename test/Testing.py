
import glob
import os
import tempfile

from rpmlint.Config import Config
from rpmlint.Pkg import FakePkg, Pkg


def testpath():
    return os.environ.get('TESTPATH', os.path.dirname(__file__))


TEST_CONFIG = os.path.join(testpath(), "configs/test.config")
CONFIG = Config(TEST_CONFIG)


def getTestedPath(path):
    return os.path.join(testpath(), path)


def getTestedPackage(name):
    pkg_path = glob.glob(getTestedPath(name) + "-*.rpm")[0]
    return Pkg(pkg_path, tempfile.gettempdir())


def getTestedSpecPackage(name):
    pkg_path = glob.glob(getTestedPath(name) + ".spec")[0]
    return FakePkg(pkg_path)
