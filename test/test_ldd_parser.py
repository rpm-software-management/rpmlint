from pathlib import Path

import pytest
from rpmlint.checks.BinariesCheck import BinariesCheck
from rpmlint.filter import Filter
from rpmlint.lddparser import LddParser
from rpmlint.pkg import FakePkg, get_magic

from Testing import CONFIG, get_tested_path, IS_X86_64


@pytest.fixture(scope='function', autouse=True)
def binariescheck():
    CONFIG.info = True
    output = Filter(CONFIG)
    test = BinariesCheck(CONFIG, output)
    return output, test


def get_full_path(path):
    return str(get_tested_path(Path('ldd', path)))


def lddparser(path, system_path=None):
    if system_path is None:
        system_path = path
    return LddParser(get_full_path(path), system_path, True)


def run_elf_checks(test, pkg, fullpath, path):
    test._detect_attributes(get_magic(fullpath))
    test.run_elf_checks(pkg, fullpath, path)


@pytest.mark.skipif(not IS_X86_64, reason='x86-64 only')
def test_unused_dependency():
    ldd = lddparser('libtirpc.so.3.0.0')
    assert not ldd.parsing_failed_reason
    assert len(ldd.unused_dependencies) >= 1
    assert 'liXXXsapi_krb5.so.2' in ldd.unused_dependencies


@pytest.mark.skipif(not IS_X86_64, reason='x86-64 only')
def test_undefined_symbol():
    ldd = lddparser('libtirpc.so.3.0.0')
    assert not ldd.parsing_failed_reason
    assert len(ldd.undefined_symbols) >= 22
    assert 'GSS_C_NT_HOSTBASED_SERVICE' in ldd.undefined_symbols


def test_ldd_parser_failure():
    ldd = lddparser('not-existing-file')
    assert 'not-existing-file: No such file or directory' in ldd.parsing_failed_reason


@pytest.mark.skipif(not IS_X86_64, reason='x86-64 only')
def test_dependencies():
    ldd = lddparser('libtirpc.so.3.0.0')
    assert not ldd.parsing_failed_reason
    assert len(ldd.dependencies) == 5
    assert any(d for d in ldd.dependencies if d.startswith('linux-vdso.so.1'))


@pytest.mark.skipif(not IS_X86_64, reason='x86-64 only')
def test_unused_dependency_in_package(binariescheck):
    output, test = binariescheck
    run_elf_checks(test, FakePkg('fake'), get_full_path('libtirpc.so.3.0.0'), '/lib64/x.so')
    assert not test.readelf_parser.parsing_failed_reason()
    assert not test.ldd_parser.parsing_failed_reason
    out = output.print_results(output.results)
    assert 'E: unused-direct-shlib-dependency ' in out


@pytest.mark.skipif(not IS_X86_64, reason='x86-64 only')
def test_unused_dependency_in_package_for_executable(binariescheck):
    output, test = binariescheck
    run_elf_checks(test, FakePkg('fake'), get_full_path('appletviewer'), '/usr/bin/appletviewer')
    assert not test.readelf_parser.parsing_failed_reason()
    assert not test.ldd_parser.parsing_failed_reason
    out = output.print_results(output.results)
    assert 'W: unused-direct-shlib-dependency ' in out


@pytest.mark.skipif(not IS_X86_64, reason='x86-64 only')
def test_opt_dependency(binariescheck):
    output, test = binariescheck
    run_elf_checks(test, FakePkg('fake'), get_full_path('opt-dependency'), '/bin/opt-dependency')
    assert not test.readelf_parser.parsing_failed_reason()
    assert not test.ldd_parser.parsing_failed_reason
    out = output.print_results(output.results)
    assert 'E: linked-against-opt-library /bin/opt-dependency /opt/libfoo.so' in out


@pytest.mark.skipif(not IS_X86_64, reason='x86-64 only')
def test_usr_dependency(binariescheck):
    output, test = binariescheck
    run_elf_checks(test, FakePkg('fake'), get_full_path('usr-dependency'), '/bin/usr-dependency')
    assert not test.readelf_parser.parsing_failed_reason()
    assert not test.ldd_parser.parsing_failed_reason
    out = output.print_results(output.results)
    assert 'W: linked-against-usr-library /bin/usr-dependency /usr/libfoo.so' in out
