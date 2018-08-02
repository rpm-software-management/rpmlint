import glob
import os

from rpmlint.Config import Config
from rpmlint.Pkg import FakePkg, Pkg


def testpath():
    return os.environ.get('TESTPATH', os.path.dirname(__file__))


TEST_CONFIG = os.path.join(testpath(), 'configs/test.config')
CONFIG = Config(TEST_CONFIG)


def get_tested_path(path):
    return os.path.join(testpath(), path)


def get_tested_package(name, testdir):
    pkg_path = glob.glob(get_tested_path(name) + '-*.rpm')[0]
    return Pkg(pkg_path, testdir)


def get_tested_spec_package(name):
    pkg_path = glob.glob(get_tested_path(name) + '.spec')[0]
    return FakePkg(pkg_path)
