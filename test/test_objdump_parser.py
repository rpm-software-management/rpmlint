from pathlib import Path

import pytest
from rpmlint.checks.BinariesCheck import BinariesCheck
from rpmlint.filter import Filter
from rpmlint.objdumpparser import ObjdumpParser
from rpmlint.pkg import FakePkg, get_magic

from Testing import CONFIG, get_tested_path, IS_X86_64


@pytest.fixture(scope='function', autouse=True)
def binariescheck():
    print(CONFIG)
    CONFIG.info = True
    output = Filter(CONFIG)
    test = BinariesCheck(CONFIG, output)
    return output, test


def get_full_path(path):
    return str(get_tested_path(Path('readelf', path)))


def objdumpparser(path, system_path=None):
    if system_path is None:
        system_path = path
    return ObjdumpParser(get_full_path(path), system_path)


def run_elf_checks(test, pkg, fullpath, path):
    test._detect_attributes(get_magic(fullpath))
    test.run_elf_checks(pkg, fullpath, path)


def test_basic():
    objdump = objdumpparser('executable-stack', '/lib64/executable-stack')
    assert not objdump.parsing_failed_reason
    assert len(objdump.compile_units) == 5
    first = objdump.compile_units[0]
    assert first['name'] == '../sysdeps/x86_64/start.S'
    assert first['comp_dir'] == '/home/abuild/rpmbuild/BUILD/glibc-2.29/csu'
    assert first['producer'] == 'GNU AS 2.32'
    assert first['language'] == '32769\t(MIPS assembler)'


@pytest.mark.skipif(not IS_X86_64, reason='x86-64 only')
def test_executable_stack_package(binariescheck):
    output, test = binariescheck
    run_elf_checks(test, FakePkg('fake'), get_full_path('executable-stack'), 'a.out')
    out = output.print_results(output.results)

    assert 'W: missing-mandatory-optflags a.out -fno-PIE -g -Ofast' in out
    assert 'E: forbidden-optflags a.out -frounding-math' in out
