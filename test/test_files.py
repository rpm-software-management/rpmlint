import re
import stat

import pytest
import rpm
from rpmlint.checks.FilesCheck import FilesCheck
from rpmlint.checks.FilesCheck import pyc_magic_from_chunk, pyc_mtime_from_chunk
from rpmlint.checks.FilesCheck import python_bytecode_to_script as pbts
from rpmlint.checks.FilesCheck import script_interpreter as se
from rpmlint.filter import Filter

from Testing import CONFIG, get_tested_mock_package, get_tested_package, get_tested_path


@pytest.fixture(scope='function', autouse=True)
def filescheck():
    CONFIG.info = True
    output = Filter(CONFIG)
    test = FilesCheck(CONFIG, output)
    yield output, test


@pytest.fixture
def output(filescheck):
    output, _test = filescheck
    yield output


@pytest.fixture
def test(filescheck):
    _output, test = filescheck
    yield test


def test_pep3147():
    assert pbts('/usr/lib64/python3.4/__pycache__/__phello__.foo.cpython-34.pyc') == '/usr/lib64/python3.4/__phello__.foo.py'
    assert pbts('/usr/lib64/python3.4/__pycache__/__phello__.foo.cpython-34.pyo') == '/usr/lib64/python3.4/__phello__.foo.py'


def test_py2():
    assert pbts('/usr/lib/python2.7/site-packages/_pytest/main.pyc') == '/usr/lib/python2.7/site-packages/_pytest/main.py'
    assert pbts('/usr/lib/python2.7/site-packages/_pytest/main.pyo') == '/usr/lib/python2.7/site-packages/_pytest/main.py'


def test_pep0488():
    assert pbts('/usr/lib/python3.5/site-packages/__pycache__/pytest.cpython-35.opt-1.pyc') == '/usr/lib/python3.5/site-packages/pytest.py'
    assert pbts('/usr/lib/python3.5/site-packages/__pycache__/pytest.cpython-35.opt-2.pyc') == '/usr/lib/python3.5/site-packages/pytest.py'
    assert pbts('/usr/lib/python3.5/site-packages/__pycache__/pytest.cpython-35.pyc') == '/usr/lib/python3.5/site-packages/pytest.py'


def chunk_from_pyc(version, size=16):
    """Helper to get start of an example pyc file as bytes"""
    path = get_tested_path(f'pyc/__future__.cpython-{version}.pyc')
    with open(path, 'rb') as f:
        return f.read(size)


@pytest.mark.parametrize('package', [get_tested_mock_package(
    files={
        '/%{unexpanded}/test': {},
        '/usr/bin/unexpanded-macro-files': {'is_dir': True},
        '/usr/share/licenses/unexpanded-macro-files': {'is_dir': True},
        '/usr/share/licenses/unexpanded-macro-files/LICENSE': {}
    },
    header={
        'requires': ['''
        /bin/bash
        bash
        rpmlib(CompressedFileNames) <= 3.0.4-1
        rpmlib(FileDigests) <= 4.6.0-1
        rpmlib(PayloadFilesHavePrefix) <= 4.0-1
        rpmlib(PayloadIsZstd) <= 5.4.18-1
        ''']}
)])
def test_unexpanded_macros(package, filescheck):
    output, test = filescheck
    test.check(package)
    out = output.print_results(output.results)
    assert 'unexpanded-macro' in out


@pytest.mark.parametrize('package', [get_tested_mock_package(
    name='python3-power',
    files={
        '/usr/lib/python3.3/site-packages/power': {'is_dir': True},
        '/usr/lib/python3.3/site-packages/power/__init__.py': {},
        '/usr/lib/python3.3/site-packages/power/__pycache__': {'is_dir': True},
        '/usr/lib/python3.3/site-packages/power/__pycache__/darwin.cpython-33.pyc': {
            'metadata': {
                'magic': ''
            }
        },
        '/usr/lib/python3.3/site-packages/power/__pycache__/darwin.cpython-33.pyo': {},
        '/usr/lib/python3.3/site-packages/power/common.py': {},
        '/usr/lib/python3.3/site-packages/power/darwin.py': {},
        '/usr/lib/python3.3/site-packages/power/linux.py': {},
        '/usr/lib/python3.3/site-packages/power/tests.py': {},
        '/usr/lib/python3.3/site-packages/power/win32.py': {},
        '/usr/share/doc/python3-power-1.1': {'is_dir': True},
        '/usr/share/doc/python3-power-1.1/darwin': {'is_dir': True},
        '/usr/share/doc/python3-power-1.1/darwin/IOPSKeys_h': {'is_dir': True},
        '/usr/share/doc/python3-power-1.1/darwin/IOPSKeys_h/index.html': {},
        '/usr/share/doc/python3-power-1.1/darwin/IOPSKeys_h/toc.html': {},
        '/usr/share/doc/python3-power-1.1/darwin/IOPowerSources_h': {'is_dir': True},
        '/usr/share/doc/python3-power-1.1/darwin/IOPowerSources_h/index.html': {},
        '/usr/share/doc/python3-power-1.1/darwin/IOPowerSources_h/toc.html': {},
        '/usr/share/doc/python3-power-1.1/linux': {'is_dir': True},
        '/usr/share/doc/python3-power-1.1/linux/power_supply.h': {},
        '/usr/share/doc/python3-power-1.1/linux/power_supply_class.txt': {},
        '/usr/share/doc/python3-power-1.1/win32': {'is_dir': True},
        '/usr/share/doc/python3-power-1.1/win32/CallNtPowerInformation.htm': {},
        '/usr/share/doc/python3-power-1.1/win32/GetSystemPowerStatus .htm': {},
        '/usr/share/doc/python3-power-1.1/win32/Power Setting GUIDs.htm': {},
        '/usr/share/doc/python3-power-1.1/win32/PowerSettingRegisterNotification.htm': {},
        '/usr/share/doc/python3-power-1.1/win32/PowerSettingUnregisterNotification.htm': {},
        '/usr/share/doc/python3-power-1.1/win32/SYSTEM_BATTERY_STATE.htm': {},
        '/usr/share/doc/python3-power-1.1/win32/SYSTEM_POWER_STATUS.htm': {},
        '/usr/lib/python3.3/site-packages/power/__pycache__/__init__.cpython-33.pyc': {
            'metadata': {
                'magic': ''
            }
        },
        '/usr/lib/python3.3/site-packages/power/__pycache__/__init__.cpython-33.pyo': {},
        '/usr/lib/python3.3/site-packages/power/__pycache__/common.cpython-33.pyc': {
            'metadata': {
                'magic': ''
            }
        },
        '/usr/lib/python3.3/site-packages/power/__pycache__/common.cpython-33.pyo': {},
        '/usr/lib/python3.3/site-packages/power/__pycache__/linux.cpython-33.pyc': {
            'metadata': {
                'magic': ''
            }
        },
        '/usr/lib/python3.3/site-packages/power/__pycache__/linux.cpython-33.pyo': {},
        '/usr/lib/python3.3/site-packages/power/__pycache__/tests.cpython-33.pyc': {
            'metadata': {
                'magic': ''
            }
        },
        '/usr/lib/python3.3/site-packages/power/__pycache__/tests.cpython-33.pyo': {},
        '/usr/lib/python3.3/site-packages/power/__pycache__/win32.cpython-33.pyc': {
            'metadata': {
                'magic': ''
            }
        },
        '/usr/lib/python3.3/site-packages/power/__pycache__/win32.cpython-33.pyo': {}
    },
    header={
        'requires': [
            'python(abi) = 3.3',
            'rpmlib(CompressedFileNames) <= 3.0.4-1',
            'rpmlib(FileDigests) <= 4.6.0-1',
            'rpmlib(PartialHardlinkSets) <= 4.0.4-1',
            'rpmlib(PayloadFilesHavePrefix) <= 4.0-1',
            'rpmlib(PayloadIsXz) <= 5.2-1'
        ]
    }
)])
def test_python_bytecode_magic(package, filescheck):
    output, test = filescheck
    test.check(package)
    # assert not output.results
    out = output.print_results(output.results)
   # assert 'python-bytecode-wrong-magic-value' not in out


@pytest.mark.parametrize('package', [get_tested_mock_package(
    name='testdocumentation',
    files={
        '/usr/share/doc/packages/testdocumentation': {'is_dir': True, 'metadata': {'mode': 0o755, 'user': 'root', 'group': 'root'}},
        '/usr/share/doc/packages/testdocumentation/README1.gz': {'metadata': {'mode': 0o644, 'user': 'root', 'group': 'root', 'flags': rpm.RPMFILE_DOC}},
        '/usr/share/doc/packages/testdocumentation/README2.bz2': {'metadata': {'mode': 0o644, 'user': 'root', 'group': 'root', 'flags': rpm.RPMFILE_DOC}},
        '/usr/share/doc/packages/testdocumentation/README3.xz': {'metadata': {'mode': 0o644, 'user': 'root', 'group': 'root', 'flags': rpm.RPMFILE_DOC}},
    },
    header={
        'requires': {
            'rpmlib(CompressedFileNames) <= 3.0.4-1',
            'rpmlib(FileDigests) <= 4.6.0-1',
            'rpmlib(PayloadFilesHavePrefix) <= 4.0-1',
            'rpmlib(PayloadIsXz) <= 5.2-1'
        }
    }
)])
def test_file_not_utf8_for_compression_algorithms(package, filescheck):
    output, test = filescheck
    test.check(package)
    out = output.print_results(output.results)
    #assert 'file-not-utf8 /usr/share/doc/packages/testdocumentation/README1.gz' in out
    #assert 'file-not-utf8 /usr/share/doc/packages/testdocumentation/README2.bz2' in out
    #assert 'file-not-utf8 /usr/share/doc/packages/testdocumentation/README3.xz' in out


@pytest.mark.parametrize('version, magic', ((36, 3379), (37, 3393)))
def test_pyc_magic_from_chunk(version, magic):
    chunk = chunk_from_pyc(version)
    assert pyc_magic_from_chunk(chunk) == magic


@pytest.mark.parametrize('version, mtime', ((36, 1513659236), (37, 1519778958)))
def test_pyc_mtime_from_chunk(version, mtime):
    chunk = chunk_from_pyc(version)
    assert pyc_mtime_from_chunk(chunk) == mtime


@pytest.mark.parametrize('package', [get_tested_mock_package(
    files={
        '/usr/src/debug/netmask-2.4.3-5.fc27.x86_64': {'is_dir': True},
        '/usr/src/debug/netmask-2.4.3-5.fc27.x86_64/LICENSE': {
            'content': '',
            'metadata': {'mode': 0o644}},
        '/usr/src/debug/netmask-2.4.3-5.fc27.x86_64/errors.c': {'metadata': {'mode': 0o644}},
        '/usr/src/debug/netmask-2.4.3-5.fc27.x86_64/errors.h': {'metadata': {'mode': 0o644}},
        '/usr/src/debug/netmask-2.4.3-5.fc27.x86_64/main.c': {'metadata': {'mode': 0o644}},
        '/usr/src/debug/netmask-2.4.3-5.fc27.x86_64/netmask.c': {'metadata': {'mode': 0o644}},
        '/usr/src/debug/netmask-2.4.3-5.fc27.x86_64/netmask.h': {'metadata': {'mode': 0o644}},
    },
    header={
        'name': 'netmask',
        'version': '2.4.3',
        'release': '5.fc27',
        'requires': [
            'rpmlib(CompressedFileNames) <= 3.0.4-1',
            'rpmlib(FileDigests) <= 4.6.0-1',
            'rpmlib(PayloadFilesHavePrefix) <= 4.0-1',
            'rpmlib(PayloadIsXz) <= 5.2-1',
        ]
    }
)])
def test_devel_files(package, filescheck):
    output, test = filescheck
    test.check(package)
    assert len(output.results) == 5
    out = output.print_results(output.results)
    assert 'devel-file-in-non-devel-package' not in out
   # assert 'incorrect-fsf-address' in out
    assert 'no-documentation' in out


@pytest.mark.parametrize('package', [get_tested_mock_package(
    files={
        '/usr/share/CMakeLists.txt': {},
        '/usr/share/Makefile.am': {'metadata': {'flags': rpm.RPMFILE_DOC}},
        '/usr/share/Makefile.in': {},
        '/usr/share/selinux': {'is_dir': True},
        '/usr/share/selinux/Makefile': {},
        '/usr/src/foo': {'is_dir': True},
        '/usr/src/foo/Makefile': {}
    },
    header={
        'requires': [
            'rpmlib(CompressedFileNames) <= 3.0.4-1',
            'rpmlib(FileDigests) <= 4.6.0-1',
            'rpmlib(PayloadFilesHavePrefix) <= 4.0-1',
            'rpmlib(PayloadIsZstd) <= 5.4.18-1'
        ]
    }
)])
def test_makefile_junk(package, filescheck):
    output, test = filescheck
    test.check(package)
    out = output.print_results(output.results)
    assert 'W: makefile-junk /usr/share/Makefile.am' in out
    assert out.count('W: makefile-junk') == 1


@pytest.mark.parametrize('package', [get_tested_mock_package(
    files={
        '/usr/lib64/python3.7/site-packages/greenlet-0.4.15-py3.7.egg-info': {},
        '/usr/lib64/python3.7/site-packages/greenlet.cpython-37m-x86_64-linux-gnu.so': {},
        '/usr/share/doc/packages/python3-greenlet': {'is_dir': True},
        '/usr/share/doc/packages/python3-greenlet/AUTHORS': {},
        '/usr/share/doc/packages/python3-greenlet/NEWS': {},
        '/usr/share/doc/packages/python3-greenlet/README.rst': {},
        '/usr/share/doc/packages/python3-greenlet/html': {'is_dir': True},
        '/usr/share/doc/packages/python3-greenlet/html/_sources': {'is_dir': True},
        '/usr/share/doc/packages/python3-greenlet/html/_sources/greenlet.txt': {},
        '/usr/share/doc/packages/python3-greenlet/html/_sources/index.txt': {},
        '/usr/share/doc/packages/python3-greenlet/html/_static': {'is_dir': True},
        '/usr/share/doc/packages/python3-greenlet/html/_static/basic.css': {},
        '/usr/share/doc/packages/python3-greenlet/html/_static/classic.css': {},
        '/usr/share/doc/packages/python3-greenlet/html/_static/default.css': {},
        '/usr/share/doc/packages/python3-greenlet/html/_static/doctools.js': {},
        '/usr/share/doc/packages/python3-greenlet/html/_static/documentation_options.js': {},
        '/usr/share/doc/packages/python3-greenlet/html/_static/file.png': {},
        '/usr/share/doc/packages/python3-greenlet/html/_static/jquery-3.2.1.js': {},
        '/usr/share/doc/packages/python3-greenlet/html/_static/jquery.js': {},
        '/usr/share/doc/packages/python3-greenlet/html/_static/language_data.js': {},
        '/usr/share/doc/packages/python3-greenlet/html/_static/minus.png': {},
        '/usr/share/doc/packages/python3-greenlet/html/_static/plus.png': {},
        '/usr/share/doc/packages/python3-greenlet/html/_static/pygments.css': {},
        '/usr/share/doc/packages/python3-greenlet/html/_static/searchtools.js': {},
        '/usr/share/doc/packages/python3-greenlet/html/_static/sidebar.js': {},
        '/usr/share/doc/packages/python3-greenlet/html/_static/underscore-1.3.1.js': {},
        '/usr/share/doc/packages/python3-greenlet/html/_static/underscore.js': {},
        '/usr/share/doc/packages/python3-greenlet/html/genindex.html': {},
        '/usr/share/doc/packages/python3-greenlet/html/greenlet.html': {},
        '/usr/share/doc/packages/python3-greenlet/html/index.html': {},
        '/usr/share/doc/packages/python3-greenlet/html/search.html': {},
        '/usr/share/licenses/python3-greenlet': {'is_dir': True},
        '/usr/share/licenses/python3-greenlet/LICENSE': {},
        '/usr/share/licenses/python3-greenlet/LICENSE.PSF': {}
    },
    header={
        'requires': [
            'libc.so.6()(64bit)',
            'libc.so.6(GLIBC_2.14)(64bit)',
            'libc.so.6(GLIBC_2.2.5)(64bit)',
            'libc.so.6(GLIBC_2.4)(64bit)',
            'libpython3.7m.so.1.0()(64bit)',
            'python(abi) = 3.7',
            'rpmlib(CompressedFileNames) <= 3.0.4-1',
            'rpmlib(FileDigests) <= 4.6.0-1',
            'rpmlib(PayloadFilesHavePrefix) <= 4.0-1',
            'rpmlib(PayloadIsXz) <= 5.2-1',
        ]
    }
)])
def test_sphinx_inv_files(package, filescheck):
    output, test = filescheck
    test.check(package)
    # assert not len(output.results)


@pytest.mark.parametrize('package', [get_tested_mock_package(
    files={
        '/.gitignore': {},
        '/.htaccess': {},
        '/bin/foo/bar': {},
        '/etc/systemd/system/foo': {},
        '/etc/tmpfiles.d/foo': {},
        '/etc/udev/rules.d/foo': {},
        '/run/foo': {},
        '/site_perl/foo': {},
        '/usr/info/dir': {},
        '/usr/share/doc/perl-foo/MANIFEST': {},
        '/~backup.rej': {}
    },
    header={ 
        'requires': [
            'rpmlib(CompressedFileNames) <= 3.0.4-1',
            'rpmlib(FileDigests) <= 4.6.0-1',
            'rpmlib(PayloadFilesHavePrefix) <= 4.0-1',
            'rpmlib(PayloadIsXz) <= 5.2-1',
        ]
    }
)])
def test_invalid_package(package, filescheck):
    output, test = filescheck
    test.check(package)
    out = output.print_results(output.results)
    assert 'W: non-ghost-in-run /run/foo' in out
    assert 'W: systemd-unit-in-etc /etc/systemd/system/foo' in out
    assert 'W: udev-rule-in-etc /etc/udev/rules.d/foo' in out
    assert 'W: tmpfiles-conf-in-etc /etc/tmpfiles.d/foo' in out
    assert 'E: subdir-in-bin /bin/foo/bar' in out
    assert 'W: siteperl-in-perl-module /site_perl/foo' in out
    assert 'E: backup-file-in-package /~backup.rej' in out
    assert 'E: version-control-internal-file /.gitignore' in out
    assert 'E: htaccess-file /.htaccess' in out
    assert 'W: manifest-in-perl-module /usr/share/doc/perl-foo/MANIFEST' in out
    assert 'E: info-dir-file /usr/info/dir' in out


@pytest.mark.parametrize('package', [get_tested_mock_package(
    files={
        '/usr/lib64/tcl/pkgIndex.tcl': {}
    },
    header={
        'requires': [
            'rpmlib(CompressedFileNames) <= 3.0.4-1',
            'rpmlib(FileDigests) <= 4.6.0-1',
            'rpmlib(PayloadFilesHavePrefix) <= 4.0-1',
            'rpmlib(PayloadIsXz) <= 5.2-1',
        ]
    }
)])
def test_tcl_package(package, filescheck):
    output, test = filescheck
    test.check(package)
    out = output.print_results(output.results)
    assert 'E: tcl-extension-file /usr/lib64/tcl/pkgIndex.tcl' in out


def test_script_interpreter():
    assert se(b'#!/bin/sh\n# Hello world!\n') == ('/bin/sh', '')
    assert se(b'#!/bin/bash -e\n') == ('/bin/bash', '-e')
    assert se(b'#! /usr/bin/perl -wT \n') == ('/usr/bin/perl', '-wT')
    assert se(b'#!/usr/bin/env python3 foo') == ('/usr/bin/env', 'python3 foo')
    assert se(b'# something here\n#!not a shebang') == (None, '')


def test_scm_regex():
    from rpmlint.checks.FilesCheck import scm_regex

    assert scm_regex.search('/foo/CVS/bar')
    assert scm_regex.search('/foo/RCS/bar')
    assert scm_regex.search('/bar/foo,v')
    assert scm_regex.search('bar/.svnignore')
    assert scm_regex.search('bar/.git/refs')


def test_lib_regex():
    from rpmlint.checks.FilesCheck import lib_regex

    # true matches
    assert all(
        lib_regex.search(x) for x in
        ('/lib/libnsl-2.26.so',
         '/usr/lib64/libgnomeui.so.3',
         '/lib64/libgcc_s.so.1'))

    # false positives
    assert not any(
        lib_regex.search(x) for x in
        ('/usr/share/gdb/auto-load/usr/lib/libglib-2.0.so.0.4600.1-gdb.py',
         '/usr/share/doc/findlib/lib-1.0.so',
         '/usr/lib64/libvulkan_radeon.so',
         '/usr/lib64/rsocket/binary',))


@pytest.mark.parametrize('package', [get_tested_mock_package(
    files={
        '/etc/bar.rs': {'content': '#![allow(box_pointers)]', 'metadata': {'mode': 0o755}},
        '/etc/foo.rs': {
            'content': '#![allow(box_pointers)]',
            'metadata': {'mode': 0o755, 'flags': rpm.RPMFILE_DOC}
        },
    },
    header={
        'requires': [
            'insserv',
            'rpmlib(CompressedFileNames) <= 3.0.4-1',
            'rpmlib(FileDigests) <= 4.6.0-1',
            'rpmlib(PayloadFilesHavePrefix) <= 4.0-1',
            'rpmlib(PayloadIsXz) <= 5.2-1',
            'xinetd',
        ]
    }
)])
def test_rust_files(package, filescheck):
    output, test = filescheck
    test.check(package)
    out = output.print_results(output.results)
   #assert 'E: wrong-script-interpreter /etc/foo.rs' in out
    assert 'E: wrong-script-interpreter /etc/bar.rs' not in out


@pytest.mark.parametrize('package', [get_tested_mock_package(
    files={
        '/etc/ngircd.conf': {},
        '/etc/pam.d/ngircd': {},
        '/usr/lib/systemd/system/ngircd.service': {},
        '/usr/sbin/ngircd': {},
        '/usr/share/doc/ngircd': {'is_dir': True},
        '/usr/share/doc/ngircd/AUTHORS': {},
        '/usr/share/doc/ngircd/Bopm.txt': {},
        '/usr/share/doc/ngircd/COPYING': {},
        '/usr/share/doc/ngircd/Capabilities.txt': {},
        '/usr/share/doc/ngircd/ChangeLog': {},
        '/usr/share/doc/ngircd/Commands.txt': {},
        '/usr/share/doc/ngircd/Contributing.txt': {},
        '/usr/share/doc/ngircd/FAQ.txt': {},
        '/usr/share/doc/ngircd/GIT.txt': {},
        '/usr/share/doc/ngircd/HowToRelease.txt': {},
        '/usr/share/doc/ngircd/Modes.txt': {},
        '/usr/share/doc/ngircd/NEWS': {},
        '/usr/share/doc/ngircd/PAM.txt': {},
        '/usr/share/doc/ngircd/Platforms.txt': {},
        '/usr/share/doc/ngircd/Protocol.txt': {},
        '/usr/share/doc/ngircd/README': {},
        '/usr/share/doc/ngircd/README-AUX.txt': {},
        '/usr/share/doc/ngircd/README-BeOS.txt': {},
        '/usr/share/doc/ngircd/README-Interix.txt': {},
        '/usr/share/doc/ngircd/RFC.txt': {},
        '/usr/share/doc/ngircd/SSL.txt': {},
        '/usr/share/doc/ngircd/Services.txt': {},
        '/usr/share/doc/ngircd/sample-ngircd.conf': {},
        '/usr/share/doc/ngircd/sample-ngircd.conf.tmpl': {},
        '/usr/share/man/man5/ngircd.conf.5.gz': {},
        '/usr/share/man/man8/ngircd.8.gz': {},
        '/var/run/ngircd': {}
    },
    header={
        'requires': ["""
            /bin/sh
            /bin/sh
            /bin/sh
            /bin/sh
            config(ngircd) = 22-2.fc22
            libc.so.6()(64bit)
            libc.so.6(GLIBC_2.14)(64bit)
            libc.so.6(GLIBC_2.15)(64bit)
            libc.so.6(GLIBC_2.2.5)(64bit)
            libc.so.6(GLIBC_2.3)(64bit)
            libc.so.6(GLIBC_2.3.2)(64bit)
            libc.so.6(GLIBC_2.3.4)(64bit)
            libc.so.6(GLIBC_2.4)(64bit)
            libgnutls.so.28()(64bit)
            libgnutls.so.28(GNUTLS_1_4)(64bit)
            libident.so.0()(64bit)
            libpam.so.0()(64bit)
            libpam.so.0(LIBPAM_1.0)(64bit)
            libwrap.so.0()(64bit)
            libz.so.1()(64bit)
            rpmlib(CompressedFileNames) <= 3.0.4-1
            rpmlib(FileDigests) <= 4.6.0-1
            rpmlib(PayloadFilesHavePrefix) <= 4.0-1
            rpmlib(PayloadIsXz) <= 5.2-1
            rtld(GNU_HASH)
            shadow-utils
            systemd
            systemd
            systemd"""]
    }
)])
def test_distribution_tags(package, filescheck):
    output, test = filescheck
    test.check(package)
    out = output.print_results(output.results)
    assert 'manpage-not-compressed' in out
    assert 'no-manual-page-for-binary' not in out
    assert 'This manual page is not compressed with the bz2 compression' in out


@pytest.mark.parametrize('package', [get_tested_mock_package(
    files={
        '/usr/x.typelib': {'content': '', 'metadata': {'mode': 0o644}}
    },
    header={
        'requires': [
            'rpmlib(CompressedFileNames) <= 3.0.4-1',
            'rpmlib(FileDigests) <= 4.6.0-1',
            'rpmlib(PayloadFilesHavePrefix) <= 4.0-1',
            'rpmlib(PayloadIsXz) <= 5.2-1'
        ]
    }
)])
def test_provides_devel(package, filescheck):
    output, test = filescheck
    test.check(package)
    out = output.print_results(output.results)
    # assert 'E: non-devel-file-in-devel-package /usr/x.typelib' in out


@pytest.mark.parametrize('package', [get_tested_mock_package(
    files={
        '/usr/lib/libfoo-2.so': {'content': '', 'metadata': {'mode': 0o755, 'user': 'root'}},
        '/usr/lib/libfoo-2.so.foo': {'content': '', 'metadata': {'mode': 0o644, 'user': 'root'}},
        '/usr/lib/libfoo.so': {'content': '', 'metadata': {'mode': 0o777, 'user': 'root'}, 'linkto': 'libfoo.so.1'},
        '/usr/lib/libfoo.so.1': {'content': '', 'metadata': {'mode': 0o755, 'user': 'root'}}
    },
    header={
        'requires': [
            'rpmlib(CompressedFileNames) <= 3.0.4-1',
            'rpmlib(FileDigests) <= 4.6.0-1',
            'rpmlib(PayloadFilesHavePrefix) <= 4.0-1',
            'rpmlib(PayloadIsXz) <= 5.2-1'
        ]
    }
)])
def test_shlib1(package, filescheck):
    output, test = filescheck
    test.check(package)
    out = output.print_results(output.results)
    #assert 'library-without-ldconfig-postin' in out
    #assert 'library-without-ldconfig-postun' in out
    assert 'devel-file-in-non-devel-package' in out


@pytest.mark.parametrize('package', [get_tested_mock_package(
    files={
        '/usr/lib/libfoo-2.so',
        '/usr/lib/libfoo-2.so.foo',
        '/usr/lib/libfoo.so',
        '/usr/lib/libfoo.so.1'
    },
    header={
        'requires': [
            'rpmlib(CompressedFileNames) <= 3.0.4-1',
            'rpmlib(FileDigests) <= 4.6.0-1',
            'rpmlib(PayloadFilesHavePrefix) <= 4.0-1',
            'rpmlib(PayloadIsXz) <= 5.2-1'
        ]}
)])
def test_shlib2_devel(package, filescheck):
    output, test = filescheck
    test.check(package)
    out = output.print_results(output.results)
    #assert 'library-without-ldconfig-postin' in out
    #assert 'library-without-ldconfig-postun' in out
    #assert 'non-devel-file-in-devel-package' in out


@pytest.mark.parametrize('package', [get_tested_mock_package(
    files={
        '/etc/security/console.apps': {'is_dir': True},
        '/etc/security/console.apps/myapp': {},
        '/usr/lib/.nosearch': {},
        '/usr/lib/emptyfile': {},
        '/usr/lib/nonemptyfile': {},
        '/usr/lib/python': {'is_dir': True},
        '/usr/lib/python/__init__.py': {},
        '/usr/lib/python/py.typed': {},
        '/usr/lib/python/pypackagefromwheel-0.0.0.dist-info': {'is_dir': True},
        '/usr/lib/python/pypackagefromwheel-0.0.0.dist-info/REQUESTED': {},
        '/usr/lib/ruby': {'is_dir': True},
        '/usr/lib/ruby/gem.build_complete': {},
        '/usr/share/doc/packages/file-zero-length': {'is_dir': True},
        '/usr/share/doc/packages/file-zero-length/dummydoc': {}
    },
    header={
        'requires': [
            'config(file-zero-length) = 1.1-0',
            'rpmlib(CompressedFileNames) <= 3.0.4-1',
            'rpmlib(FileDigests) <= 4.6.0-1',
            'rpmlib(PayloadFilesHavePrefix) <= 4.0-1',
            'rpmlib(PayloadIsZstd) <= 5.4.18-1'
        ]
    }
)])
@pytest.mark.parametrize(
    'filename, show',
    [('/usr/lib/emptyfile', True),
     ('/usr/lib/nonemptyfile', False),
     ('/etc/security/console.apps', False),
     ('/usr/lib/.nosearch', False),
     ('/usr/lib/python/__init__.py', False),
     ('/usr/lib/python/py.typed', False),
     ('/usr/lib/python/pypackagefromwheel-0.0.0.dist-info/REQUESTED', False),
     ('/usr/lib/ruby/gem.build_complete', False)])
def test_zero_length_ignore(package, filescheck, filename, show):
    output, test = filescheck
    pkg = package
    test.check(pkg)
    out = output.print_results(output.results)
    #assert filename in pkg.files
    #assert (f'zero-length {filename}' in out) == show


@pytest.mark.parametrize('package', [get_tested_mock_package(
    files={
        '/usr/share/man/man0p': {'is_dir': True},
        '/usr/share/man/man0p/foo.3.gz': {},
        '/usr/share/man/man1': {'is_dir': True},
        '/usr/share/man/man1/test.1.zst': {},
        '/usr/share/man/man3': {'is_dir': True},
        '/usr/share/man/man3/foo': {'is_dir': True},
        '/usr/share/man/man3/foo/bar': {'is_dir': True},
        '/usr/share/man/man3/foo/bar/baz.3.gz': {},
        '/usr/share/man/man3/some.3pm.gz': {}
    },
    header={
        'requires': [
            'rpmlib(CompressedFileNames) <= 3.0.4-1',
            'rpmlib(FileDigests) <= 4.6.0-1',
            'rpmlib(PayloadFilesHavePrefix) <= 4.0-1',
            'rpmlib(PayloadIsZstd) <= 5.4.18-1'
        ]
    }
)])
def test_manual_pages(package, filescheck):
    output, test = filescheck
    test.check(package)
    out = output.print_results(output.results)
    assert 'E: manual-page-in-subfolder /usr/share/man/man3/foo/bar/baz.3.gz' in out
    assert 'W: manpage-not-compressed bz2 /usr/share/man/man1/test.1.zst' in out
    assert 'E: bad-manual-page-folder /usr/share/man/man0p/foo.3.gz expected folder: man3' in out
    assert 'bad-manual-page-folder /usr/share/man/man3/some.3pm.gz' not in out


@pytest.mark.parametrize('package', [
    get_tested_mock_package(
        files={
            '/usr/share/package/bin.py': {
                'content': '#!/usr/bin/python3\nprint("python required")',
                'metadata': {'mode': 0o755 | stat.S_IFREG},
            },
            '/usr/bin/testlink': {
                'linkto': '../share/package/bin.py',
            },
        },
        header={},
    ),
])
def test_shebang(package, output, test):
    test.check(package)
    out = output.print_results(output.results)
    assert 'W: symlink-to-binary-with-shebang /usr/bin/testlink' in out


@pytest.mark.parametrize('package', [
    get_tested_mock_package(
        files={
            '/usr/share/package/bin.py': {
                'content': '#!/usr/bin/python3\nprint("python required")',
                'metadata': {'mode': 0o755 | stat.S_IFREG},
            },
            '/usr/bin/testlink': {
                'linkto': '../share/package/bin.py',
            },
        },
        header={
            'requires': ['/usr/bin/python3'],
        },
    ),
])
def test_shebang_ok(package, output, test):
    test.check(package)
    out = output.print_results(output.results)
    assert 'W: symlink-to-binary-with-shebang /usr/bin/testlink' not in out


@pytest.mark.parametrize('package', [
    get_tested_mock_package(
        header={'requires': []},
        files={
            '/etc/raddb/mods-config/sql/moonshot-targeted-ids/mysql': {
                'is_dir': True,
                'metadata': {'mode': 0o640 | stat.S_IFDIR},
            },
            '/etc/raddb/mods-config/sql/moonshot-targeted-ids/postgresql': {
                'is_dir': True,
                'metadata': {'mode': 0o640 | stat.S_IFDIR},
            },
            '/etc/raddb/mods-config/sql/moonshot-targeted-ids/sqlite': {
                'is_dir': True,
                'metadata': {'mode': 0o640 | stat.S_IFDIR},
            },
        },
    ),
])
def test_directory_without_x_permission(package, output, test):
    test.check(package)
    out = output.print_results(output.results)
    assert 'E: non-standard-dir-perm' in out


# LOTS OF FILES
@pytest.mark.parametrize('package', ['binary/freeradius-server'])
def test_directory_without_x_permission2(tmp_path, package, filescheck):
    output, test = filescheck
    test.check(get_tested_package(package, tmp_path))
    out = output.print_results(output.results)
    assert 'E: non-standard-dir-perm' in out


@pytest.mark.parametrize('package', [
    get_tested_mock_package(
        header={'requires': []},
        files={
            '/var/lib/pipewire': {'is_dir': True, 'metadata': {'mode': 0o000 | stat.S_IFDIR}},
            '/var/lib/dir_read': {'is_dir': True, 'metadata': {'mode': 0o755 | stat.S_IFDIR}},
            '/var/lib/pipewire/ghost_file': {'metadata': {'mode': 0o000, 'flags': rpm.RPMFILE_GHOST}},
            '/var/lib/pipewire/ghost_file_read': {'metadata': {'mode': 0o644, 'flags': rpm.RPMFILE_GHOST}},
            '/var/lib/pipewire/normal_file': {'metadata': {'mode': 0o000}},
            '/var/lib/pipewire/normal_file_read': {'metadata': {'mode': 0o644}},
        },
    ),
])
def test_files_without_perms(package, output, test):
    test.check(package)
    out = output.print_results(output.results)
    assert re.findall('W: zero-perms .*pipewire ', out)
    assert re.findall('W: zero-perms-ghost .*ghost_file', out)
    assert re.findall('W: zero-perms .*normal_file ', out)
    assert not re.findall('W: zero-perms .*normal_file_read ', out)
    assert not re.findall('W: zero-perms .*dir_read ', out)
    assert not re.findall('W: zero-perms-ghost .*ghost_file_read', out)


@pytest.mark.parametrize('package', [
    get_tested_mock_package(
        header={'requires': []},
        files={
            '/run/netconfig/resolv.conf': {'metadata': {'mode': 0o000, 'flags': rpm.RPMFILE_GHOST}},
            '/run/netconfig/yp.conf': {'metadata': {'mode': 0o644, 'flags': rpm.RPMFILE_GHOST}},
            '/run/netconfig': {'is_dir': True, 'metadata': {'mode': 0o000, 'flags': rpm.RPMFILE_GHOST | stat.S_IFDIR}},
            '/usr/lib/tmpfiles.d/netconfig.conf': {
                'content': """
d /run/netconfig 0755 root group -
f /run/netconfig/resolv.conf 0644 root root -
f /run/netconfig/yp.conf 0644 root root -
"""
            },
        },
    ),
])
def test_files_without_perms_tmpfiles(package, output, test):
    test.check(package)
    out = output.print_results(output.results)
    assert re.findall(r'W: zero-perms-ghost .*"%ghost %attr\(0644,root,root\) .*resolv.conf"', out)
    assert re.findall(r'W: zero-perms-ghost .*"%ghost %attr\(0755,root,group\) /run/netconfig"', out)
    assert not re.findall('W: zero-perms.*yp.conf ', out)
