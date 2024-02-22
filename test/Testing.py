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


def _testpath():
    return Path(os.environ.get('TESTPATH', Path(__file__).parent))


TEST_CONFIG = [_testpath() / 'configs/test.config']
CONFIG = Config(TEST_CONFIG)

# predicates used for pytest.mark.skipif decorators
IS_X86_64 = platform.machine() == 'x86_64'
IS_I686 = re.match(platform.machine(), 'i[3456]86')
IS_FEDORA_RELEASE = os.path.exists('/etc/fedora-release')
HAS_32BIT_GLIBC = glob.glob('/lib/ld-linux.so.*')
HAS_CHECKBASHISMS = shutil.which('checkbashisms')
HAS_DASH = shutil.which('dash')
HAS_DESKTOP_FILE_UTILS = shutil.which('desktop-file-validate')
HAS_APPSTREAM_GLIB = shutil.which('appstream-util')

RPMDB_PATH = subprocess.run(['rpm', '--eval', '%_dbpath'], encoding='utf8', stdout=subprocess.PIPE).stdout
HAS_RPMDB = RPMDB_PATH and Path(RPMDB_PATH.strip()).exists()


def _has_dictionary(language):
    if not rpmlint.spellcheck.ENCHANT:
        return False
    spell = rpmlint.spellcheck.Spellcheck()
    spell._init_checker(language)
    return spell._enchant_checkers.get(language)


HAS_ENGLISH_DICTIONARY = _has_dictionary('en_US')
HAS_CZECH_DICTIONARY = _has_dictionary('cs_CZ')
HAS_FRENCH_DICTIONARY = _has_dictionary('fr')


def get_tested_path(*paths):
    return _testpath().joinpath(*paths)


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


class LazyMock:
    """
    Class to store mock package definition and create the actual mock package
    when needed, when some internal attribute or method is requested.
    """

    def __init__(self, files, header, name):
        self._lazy_pkg = None
        self._lazy_files = files
        self._lazy_header = header
        self._lazy_name = name

    @property
    def _fake_pkg(self):
        if not self._lazy_pkg:
            self._lazy_pkg = get_tested_mock_package(self._lazy_files,
                                                     self._lazy_header,
                                                     self._lazy_name)
        return self._lazy_pkg

    def clone(self, files=None, header=None, name=None):
        """
        Copies this LazyMock modifying some properties
        """

        if files is None:
            files = self._lazy_files
        if header is None:
            header = self._lazy_header
        if name is None:
            name = self._lazy_name

        return LazyMock(files, header, name)

    def __getitem__(self, key):
        return self._fake_pkg.__getitem__(key)

    def __getattr__(self, name):
        return getattr(self._fake_pkg, name)


def get_tested_mock_package(files=None, header=None, name='mockPkg', lazyload=False):
    if lazyload:
        return LazyMock(files, header, name)

    mockPkg = FakePkg(name)
    if files is not None:
        if isinstance(files, dict):
            # full path for test files
            for attrs in files.values():
                if 'content-path' in attrs:
                    attrs['content-path'] = get_tested_path(attrs['content-path'])

        mockPkg.create_files(files)
    if header is not None:
        mockPkg.add_header(header)
    mockPkg.initiate_files_base_data()
    return mockPkg
