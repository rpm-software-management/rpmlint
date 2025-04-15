import re

from mockdata.mock_files import (
    DevelopmentPackage,
    DirectoryWithoutXPerm2Package,
    DirectoryWithoutXPermPackage,
    FileChecksPackage,
    FilesWithoutPermsPackage,
    FilesWithoutPermsTmpfilesPackage,
    FileZeroLengthPackage,
    IncorrectFSFAddress,
    MakefileJunkPackage,
    ManPagesPackage,
    ManualPagesPackage,
    NetmaskDebugsourcePackage,
    NonReadableGhostPackage,
    Python3PowerBrokenPackage,
    Python3PowerPackage,
    PythonShebangLinkOkPackage,
    PythonShebangLinkPackage,
    RustFilesPackage,
    Shlib1Package,
    Shlib2DevelPackage,
    SphinxInvPackage,
    TclPackage,
    TestDocumentationPackage,
    UnexpandedMacroFilesPackage,
)
import pytest
from rpmlint.checks.FilesCheck import FilesCheck
from rpmlint.checks.FilesCheck import pyc_magic_from_chunk, pyc_mtime_from_chunk
from rpmlint.checks.FilesCheck import python_bytecode_to_script as pbts
from rpmlint.checks.FilesCheck import script_interpreter as se
from rpmlint.filter import Filter

from Testing import CONFIG, get_tested_path


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


@pytest.mark.parametrize('package', [UnexpandedMacroFilesPackage])
def test_unexpanded_macros(package, filescheck):
    output, test = filescheck
    test.check(package)
    out = output.print_results(output.results)
    assert 'unexpanded-macro' in out


@pytest.mark.parametrize('package,result', [
    (Python3PowerPackage, False),
    (Python3PowerBrokenPackage, True),
])
def test_python_bytecode_magic(package, result, filescheck):
    output, test = filescheck
    test.check(package)
    out = output.print_results(output.results)
    assert ('python-bytecode-wrong-magic-value' in out) == result


@pytest.mark.parametrize('package', [TestDocumentationPackage])
def test_file_not_utf8_for_compression_algorithms(package, filescheck):
    output, test = filescheck
    test.check(package)
    out = output.print_results(output.results)
    assert 'file-not-utf8 /usr/share/doc/packages/testdocumentation/README1.gz' in out
    assert 'file-not-utf8 /usr/share/doc/packages/testdocumentation/README2.bz2' in out
    assert 'file-not-utf8 /usr/share/doc/packages/testdocumentation/README3.xz' in out


@pytest.mark.parametrize('version, magic', ((36, 3379), (37, 3393)))
def test_pyc_magic_from_chunk(version, magic):
    chunk = chunk_from_pyc(version)
    assert pyc_magic_from_chunk(chunk) == magic


@pytest.mark.parametrize('version, mtime', ((36, 1513659236), (37, 1519778958)))
def test_pyc_mtime_from_chunk(version, mtime):
    chunk = chunk_from_pyc(version)
    assert pyc_mtime_from_chunk(chunk) == mtime


@pytest.mark.parametrize('package', [NetmaskDebugsourcePackage])
def test_devel_files(package, filescheck):
    output, test = filescheck
    test.check(package)
    assert len(output.results) == 5
    out = output.print_results(output.results)
    assert 'devel-file-in-non-devel-package' not in out
    assert 'incorrect-fsf-address' in out
    assert 'no-documentation' in out


@pytest.mark.parametrize('package', [IncorrectFSFAddress])
def test_incorrect_fsf_address(package, filescheck):
    output, test = filescheck
    test.check(package)
    out = output.print_results(output.results)
    assert 'incorrect-fsf-address /usr/incorrect-fsf.txt' in out
    assert 'incorrect-fsf-address /usr/correct-fsf.txt' not in out


@pytest.mark.parametrize('package', [MakefileJunkPackage])
def test_makefile_junk(package, filescheck):
    output, test = filescheck
    test.check(package)
    out = output.print_results(output.results)
    assert 'W: makefile-junk /usr/share/Makefile.am' in out
    assert out.count('W: makefile-junk') == 1


@pytest.mark.parametrize('package', [SphinxInvPackage])
def test_sphinx_inv_files(package, filescheck):
    output, test = filescheck
    test.check(package)
    assert not len(output.results)


@pytest.mark.parametrize('package', [FileChecksPackage])
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


@pytest.mark.parametrize('package', [TclPackage])
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


@pytest.mark.parametrize('package', [RustFilesPackage])
def test_rust_files(package, filescheck):
    output, test = filescheck
    test.check(package)
    out = output.print_results(output.results)
    assert 'E: wrong-script-interpreter /etc/foo.rs' in out
    assert 'E: wrong-script-interpreter /etc/bar.rs' not in out


@pytest.mark.parametrize('package', [ManPagesPackage])
def test_manpages(package, filescheck):
    output, test = filescheck
    test.check(package)
    out = output.print_results(output.results)
    assert 'manpage-not-compressed' in out
    assert 'no-manual-page-for-binary' not in out
    assert 'This manual page is not compressed with the bz2 compression' in out


@pytest.mark.parametrize('package', [DevelopmentPackage])
def test_provides_devel(package, filescheck):
    output, test = filescheck
    test.check(package)
    out = output.print_results(output.results)
    assert 'E: non-devel-file-in-devel-package /usr/x.typelib' in out


@pytest.mark.parametrize('package,is_devel', [
    (Shlib1Package, False),
    (Shlib2DevelPackage, True),
])
def test_shlib(package, is_devel, filescheck):
    output, test = filescheck
    test.check(package)
    out = output.print_results(output.results)
    assert 'library-without-ldconfig-postin' in out
    assert 'library-without-ldconfig-postun' in out
    if is_devel:
        assert ('non-devel-file-in-devel-package' in out)
    else:
        assert ('devel-file-in-non-devel-package' in out)


@pytest.mark.parametrize('package, files', [
    (FileZeroLengthPackage, [
        ('/usr/lib/emptyfile', True),
        ('/usr/lib/nonemptyfile', False),
        ('/etc/security/console.apps', False),
        ('/etc/security/console.apps/myapp', False),
        ('/usr/lib/.nosearch', False),
        ('/etc/share/doc/packages/file-zero-length/dummydoc', False),
        ('/usr/lib/python/__init__.py', False),
        ('/usr/lib/python/py.typed', False),
        ('/usr/lib/python/pypackagefromwheel-0.0.0.dist-info/REQUESTED', False),
        ('/usr/lib/ruby/gem.build_complete', False),
    ]),
])
def test_zero_length_ignore(package, files, filescheck):
    output, test = filescheck
    test.check(package)
    out = output.print_results(output.results)
    for filename, show in files:
        assert filename in package.files
        assert (f'zero-length {filename}' in out) == show


@pytest.mark.parametrize('package', [ManualPagesPackage])
def test_manual_pages(package, filescheck):
    output, test = filescheck
    test.check(package)
    out = output.print_results(output.results)
    assert 'E: manual-page-in-subfolder /usr/share/man/man3/foo/bar/baz.3.gz' in out
    assert 'W: manpage-not-compressed bz2 /usr/share/man/man1/test.1.zst' in out
    assert 'E: bad-manual-page-folder /usr/share/man/man0p/foo.3.gz expected folder: man3' in out
    assert 'E: bad-manual-page-folder /usr/share/man/man3/some.3pm.gz' not in out


@pytest.mark.parametrize('package,is_ok', [
    (PythonShebangLinkPackage, False),
    (PythonShebangLinkOkPackage, True),
])
def test_shebang(package, is_ok, output, test):
    test.check(package)
    out = output.print_results(output.results)
    assert ('W: symlink-to-binary-with-shebang /usr/bin/testlink' not in out) == is_ok


@pytest.mark.parametrize('package, is_ok', [
    (DirectoryWithoutXPermPackage, False),
    (DirectoryWithoutXPerm2Package, False),
])
def test_directory_without_x_permission(package, is_ok, output, test):
    test.check(package)
    out = output.print_results(output.results)
    assert ('E: non-standard-dir-perm' not in out) == is_ok


@pytest.mark.parametrize('package', [FilesWithoutPermsPackage])
def test_files_without_perms(package, output, test):
    test.check(package)
    out = output.print_results(output.results)
    assert re.findall('W: zero-perms .*pipewire ', out)
    assert re.findall('W: zero-perms-ghost .*ghost_file', out)
    assert re.findall('W: zero-perms .*normal_file ', out)
    assert not re.findall('W: zero-perms .*normal_file_read ', out)
    assert not re.findall('W: zero-perms .*dir_read ', out)
    assert not re.findall('W: zero-perms-ghost .*ghost_file_read', out)


@pytest.mark.parametrize('package', [FilesWithoutPermsTmpfilesPackage])
def test_files_without_perms_tmpfiles(package, output, test):
    test.check(package)
    out = output.print_results(output.results)
    assert re.findall(r'W: zero-perms-ghost .*"%ghost %attr\(0644,root,root\) .*resolv.conf"', out)
    assert re.findall(r'W: zero-perms-ghost .*"%ghost %attr\(0755,root,group\) /run/netconfig"', out)
    assert not re.findall('W: zero-perms.*yp.conf ', out)


# https://github.com/rpm-software-management/rpmlint/issues/1287
@pytest.mark.parametrize('package', [NonReadableGhostPackage])
def test_non_readable_ghost_files(package, output, test):
    test.check(package)
    out = output.print_results(output.results)
    assert 'E: non-readable /boohoo 0' not in out
