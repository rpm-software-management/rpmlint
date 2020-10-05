import os
from pathlib import Path

from rpmlint.config import Config
from rpmlint.pkg import FakePkg, Pkg


def testpath():
    return Path(os.environ.get('TESTPATH', Path(__file__).parent))


TEST_CONFIG = [testpath() / 'configs/test.config']
CONFIG = Config(TEST_CONFIG)


def get_tested_path(path):
    return testpath() / path


def get_tested_package(name, testdir):
    filename = Path(name).name + '-*.rpm'
    candidates = list(get_tested_path(name).parent.glob(filename))
    assert len(candidates) == 1
    return Pkg(candidates[0], testdir)


def get_tested_spec_package(name):
    filename = Path(name).name + '.spec'
    candidates = list(get_tested_path(name).parent.glob(filename))
    assert len(candidates) == 1
    return FakePkg(candidates[0])
