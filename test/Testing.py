import glob
import os
from pathlib import Path
import platform
import re
import shutil
import subprocess

import rpm
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
HAS_32BIT_GLIBC = glob.glob('/lib/ld-linux.so.*')
HAS_CHECKBASHISMS = shutil.which('checkbashisms')
HAS_DASH = shutil.which('dash')
HAS_DESKTOP_FILE_UTILS = shutil.which('desktop-file-validate')
HAS_APPSTREAM_GLIB = shutil.which('appstream-util')

RPMDB_PATH = subprocess.run(['rpm', '--eval', '%_dbpath'], encoding='utf8', stdout=subprocess.PIPE).stdout
# The db path may exist while the database itself is empty (e.g. rpm
# installed on a non-rpm distro); installed-package tests need entries.
HAS_RPMDB = bool(RPMDB_PATH and Path(RPMDB_PATH.strip()).exists() and
                 len(list(rpm.TransactionSet().dbMatch())) > 0)


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


def build_tiny_rpm(tmp_path, name, version='1.0', install_script='', files_list='',
                   summary='test package'):
    """
    Build a tiny noarch RPM at test time with rpmbuild.

    install_script runs as the %install section body (with %{buildroot}
    available), files_list is the %files section body.
    Returns the path of the built RPM.
    """
    topdir = tmp_path / 'rpmbuild'
    for subdir in ('BUILD', 'RPMS', 'SOURCES', 'SPECS', 'SRPMS'):
        (topdir / subdir).mkdir(parents=True, exist_ok=True)
    spec = topdir / 'SPECS' / f'{name}.spec'
    spec.write_text(
        f'Name:           {name}\n'
        f'Version:        {version}\n'
        'Release:        0\n'
        f'Summary:        {summary}\n'
        'License:        MIT\n'
        'BuildArch:      noarch\n'
        '\n'
        '%description\n'
        'test package\n'
        '\n'
        '%install\n'
        f'{install_script}\n'
        '\n'
        '%files\n'
        f'{files_list}\n'
    )
    proc = subprocess.run(
        ['rpmbuild', '-bb',
         '--define', f'_topdir {topdir}',
         # Pin _rpmdir as well: it may be overridden by system or user
         # rpm configuration, which would redirect the built RPM away
         # from topdir/RPMS while rpmbuild still exits successfully.
         '--define', f'_rpmdir {topdir}/RPMS',
         str(spec)],
        capture_output=True, text=True,
    )
    assert proc.returncode == 0, \
        f'rpmbuild failed:\n{proc.stdout}\n{proc.stderr}'
    # Ask rpmbuild where it put the RPM instead of assuming a directory:
    # macro configuration (e.g. in mock chroots) may redirect it.
    rpms = [line.split('Wrote: ', 1)[1].strip()
            for line in proc.stdout.splitlines()
            if line.startswith('Wrote: ') and line.rstrip().endswith('.rpm')]
    if not rpms:
        # Fall back to searching topdir, e.g. for localized rpmbuild output.
        rpms = [str(path) for path in (topdir / 'RPMS').rglob('*.rpm')]
    assert len(rpms) == 1, \
        f'expected one RPM, got {rpms}:\n{proc.stdout}\n{proc.stderr}'
    return Path(rpms[0])


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

    def clone(self, files=None, header=None, name=None, extend=False):
        """
        Copies this LazyMock modifying some properties
        """

        if files is None:
            files = self._lazy_files
        if header is None:
            header = self._lazy_header
        elif extend:
            header = self._lazy_header | header
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
