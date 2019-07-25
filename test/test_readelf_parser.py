import os

import pytest
from rpmlint.checks.BinariesCheck import BinariesCheck
from rpmlint.filter import Filter
from rpmlint.pkg import FakePkg
from rpmlint.readelfparser import ReadelfParser

from Testing import CONFIG, get_tested_path


@pytest.fixture(scope='function', autouse=True)
def binariescheck():
    CONFIG.info = True
    output = Filter(CONFIG)
    test = BinariesCheck(CONFIG, output)
    return output, test


def get_full_path(path):
    return str(get_tested_path(os.path.join('readelf', path)))


def readelfparser(path):
    return ReadelfParser(get_full_path(path))


def test_empty_archive():
    readelf = readelfparser('empty-archive.a')
    assert len(readelf.section_info.elf_files) == 0


def test_simple_archive():
    readelf = readelfparser('main.a')
    assert len(readelf.section_info.elf_files) == 1
    elf_file = readelf.section_info.elf_files[0]
    assert len(elf_file) == 11
    assert elf_file[0].name == '.text'
    assert elf_file[0].size == 21


def test_program_header_parsing():
    readelf = readelfparser('nested-function')
    assert len(readelf.program_header_info.headers) == 11
    h0 = readelf.program_header_info.headers[0]
    assert h0.name == 'PHDR'
    assert h0.flags == 'R'
    h9 = readelf.program_header_info.headers[9]
    assert h9.name == 'GNU_STACK'
    assert h9.flags == 'RWE'


def test_lto_bytecode(binariescheck):
    output, test = binariescheck
    test.run_elf_checks(FakePkg('fake'), get_full_path('lto-object.o'), 'x.a')
    assert not test.readelf_parser.parsing_failed()
    out = output.print_results(output.results)
    'lto-bytecode' in out


def test_lto_archive_text(binariescheck):
    output, test = binariescheck
    test.run_elf_checks(FakePkg('fake'), get_full_path('stripped-lto.a'), 'x.a')
    assert len(output.results) == 1
    assert 'E: lto-no-text-in-archive' in output.results[0]


def test_readelf_failure():
    readelf = readelfparser('no-existing-file')
    assert readelf.parsing_failed
