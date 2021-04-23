import pytest
from rpmlint.checks.FilesCheck import FilesCheck
from rpmlint.checks.FilesCheck import pyc_magic_from_chunk, pyc_mtime_from_chunk
from rpmlint.checks.FilesCheck import python_bytecode_to_script as pbts
from rpmlint.checks.FilesCheck import script_interpreter as se
from rpmlint.filter import Filter

from Testing import CONFIG, get_tested_package, get_tested_path


@pytest.fixture(scope='function', autouse=True)
def filescheck():
    CONFIG.info = True
    output = Filter(CONFIG)
    test = FilesCheck(CONFIG, output)
    return output, test


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
    path = get_tested_path('pyc/__future__.cpython-{}.pyc'.format(version))
    with open(path, 'rb') as f:
        return f.read(size)


@pytest.mark.parametrize('package', ['binary/python3-power'])
def test_python_bytecode_magic(tmpdir, package, filescheck):
    output, test = filescheck
    test.check(get_tested_package(package, tmpdir))
    assert not output.results
    out = output.print_results(output.results)
    assert 'python-bytecode-wrong-magic-value' not in out


@pytest.mark.parametrize('package', ['binary/testdocumentation'])
def test_file_not_utf8_for_compression_algorithms(tmpdir, package, filescheck):
    output, test = filescheck
    test.check(get_tested_package(package, tmpdir))
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


@pytest.mark.parametrize('package', ['binary/netmask-debugsource'])
def test_devel_files(tmpdir, package, filescheck):
    output, test = filescheck
    test.check(get_tested_package(package, tmpdir))
    assert len(output.results) == 5
    out = output.print_results(output.results)
    assert 'devel-file-in-non-devel-package' not in out
    assert 'incorrect-fsf-address' in out
    assert 'no-documentation' in out


@pytest.mark.parametrize('package', ['binary/makefile-junk'])
def test_makefile_junk(tmpdir, package, filescheck):
    output, test = filescheck
    test.check(get_tested_package(package, tmpdir))
    out = output.print_results(output.results)
    assert 'W: makefile-junk /usr/share/Makefile.am' in out
    assert out.count('W: makefile-junk') == 1


@pytest.mark.parametrize('package', ['binary/python3-greenlet'])
def test_sphinx_inv_files(tmpdir, package, filescheck):
    output, test = filescheck
    test.check(get_tested_package(package, tmpdir))
    assert not len(output.results)


@pytest.mark.parametrize('package', ['binary/filechecks'])
def test_invalid_package(tmpdir, package, filescheck):
    output, test = filescheck
    test.check(get_tested_package(package, tmpdir))
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


@pytest.mark.parametrize('package', ['binary/tclpackage'])
def test_tcl_package(tmpdir, package, filescheck):
    output, test = filescheck
    test.check(get_tested_package(package, tmpdir))
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


@pytest.mark.parametrize('package', ['binary/rust'])
def test_rust_files(tmpdir, package, filescheck):
    output, test = filescheck
    test.check(get_tested_package(package, tmpdir))
    out = output.print_results(output.results)
    assert 'E: wrong-script-interpreter /etc/foo.rs' in out
    assert 'E: wrong-script-interpreter /etc/bar.rs' not in out


@pytest.mark.parametrize('package', ['binary/ngircd'])
def test_distribution_tags(tmpdir, package, filescheck):
    output, test = filescheck
    test.check(get_tested_package(package, tmpdir))
    out = output.print_results(output.results)
    assert 'manpage-not-compressed' in out
    assert 'This manual page is not compressed with the bz2 compression' in out


@pytest.mark.parametrize('package', ['binary/development'])
def test_provides_devel(tmpdir, package, filescheck):
    output, test = filescheck
    test.check(get_tested_package(package, tmpdir))
    out = output.print_results(output.results)
    assert 'E: non-devel-file-in-devel-package /usr/x.typelib' in out


@pytest.mark.parametrize('package', ['binary/shlib1'])
def test_shlib1(tmpdir, package, filescheck):
    output, test = filescheck
    test.check(get_tested_package(package, tmpdir))
    out = output.print_results(output.results)
    assert 'library-without-ldconfig-postin' in out
    assert 'library-without-ldconfig-postun' in out
    assert 'devel-file-in-non-devel-package' in out


@pytest.mark.parametrize('package', ['binary/shlib2-devel'])
def test_shlib2_devel(tmpdir, package, filescheck):
    output, test = filescheck
    test.check(get_tested_package(package, tmpdir))
    out = output.print_results(output.results)
    assert 'library-without-ldconfig-postin' in out
    assert 'library-without-ldconfig-postun' in out
    assert 'non-devel-file-in-devel-package' in out


@pytest.mark.parametrize('package', ['binary/file-zero-length'])
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
def test_zero_length_ignore(tmpdir, package, filescheck, filename, show):
    output, test = filescheck
    pkg = get_tested_package(package, tmpdir)
    test.check(pkg)
    out = output.print_results(output.results)
    assert filename in pkg.files
    assert (f'zero-length {filename}' in out) == show
