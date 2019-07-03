import os
from pathlib import Path

from rpmlint.config import Config
from rpmlint.pkg import FakePkg, Pkg


def testpath():
    return Path(os.environ.get('TESTPATH', Path(__file__).parent))


TEST_CONFIG = testpath() / 'configs/test.config'
CONFIG = Config(TEST_CONFIG)


def get_tested_path(path):
    return testpath() / path


def get_tested_package(name, testdir):
    pkg_path = list(get_tested_path(name).parent.glob(name.split('/')[-1] + '-*.rpm'))[0]
    return Pkg(pkg_path, testdir)


def get_tested_spec_package(name):
    pkg_path = list(get_tested_path(name).parent.glob(name.split('/')[-1] + '.spec'))[0]
    return FakePkg(pkg_path)
