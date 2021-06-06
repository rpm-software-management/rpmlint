import glob
import os
from pathlib import Path
import platform
import re
import shutil
import subprocess

from rpmlint.config import Config
from rpmlint.pkg import FakePkg, Pkg
import rpmlint.spellcheck


def testpath():
    return Path(os.environ.get('TESTPATH', Path(__file__).parent))


TEST_CONFIG = [testpath() / 'configs/test.config']
CONFIG = Config(TEST_CONFIG)

# predicates used for pytest.mark.skipif decorators
IS_X86_64 = platform.machine() == 'x86_64'
IS_I686 = re.match(platform.machine(), 'i[3456]86')
HAS_32BIT_GLIBC = glob.glob('/lib/ld-linux.so.*')
HAS_CHECKBASHISMS = shutil.which('checkbashisms')
HAS_DASH = shutil.which('dash')
HAS_DESKTOP_FILE_UTILS = shutil.which('desktop-file-validate')
HAS_APPSTREAM_GLIB = shutil.which('appstream-util')

RPMDB_PATH = subprocess.run(['rpm', '--eval', '"%_dbpath"'], encoding='utf8').stdout
HAS_RPMDB = RPMDB_PATH and Path(RPMDB_PATH).exists()


def _has_dictionary(language):
    if not rpmlint.spellcheck.ENCHANT:
        return False
    spell = rpmlint.spellcheck.Spellcheck()
    spell._init_checker(language)
    return (
        language in spell._enchant_checkers and
        spell._enchant_checkers[language] is not None
    )


HAS_ENGLISH_DICTIONARY = _has_dictionary('en_US')
HAS_CZECH_DICTIONARY = _has_dictionary('cs_CZ')


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
