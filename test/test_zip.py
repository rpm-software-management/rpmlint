import pytest
from rpmlint.checks.ZipCheck import ZipCheck
from rpmlint.filter import Filter

from Testing import CONFIG, get_tested_package


@pytest.fixture(scope='function', autouse=True)
def zipcheck():
    CONFIG.info = True
    output = Filter(CONFIG)
    test = ZipCheck(CONFIG, output)
    return output, test


@pytest.mark.parametrize('package', ['binary/bad-crc-uncompressed'])
def test_bad_crc_and_compression(tmpdir, package, zipcheck):
    output, test = zipcheck
    test.check(get_tested_package(package, tmpdir))
    out = output.print_results(output.results)

    assert 'bad-crc-in-zip' in out
    assert 'zip fails the CRC check' in out

    assert 'uncompressed-zip' in out
    assert 'zip file is not compressed' in out


@pytest.mark.parametrize('package', ['binary/asm'])
def test_classpath_and_index(tmpdir, package, zipcheck):
    output, test = zipcheck
    test.check(get_tested_package(package, tmpdir))
    out = output.print_results(output.results)
    assert 'class-path-in-manifest' in out
    assert 'jar contains a hardcoded Class-Path' in out

    assert 'jar-not-indexed' in out
    assert 'jar file is not indexed' in out


@pytest.mark.parametrize('package', ['binary/ruby2.5-rubygem-rubyzip-testsuite'])
def test_zip1(tmpdir, package, zipcheck):
    output, test = zipcheck
    test.check(get_tested_package(package, tmpdir))
    out = output.print_results(output.results)
    # these are PW protected not broken so do not error about them
    assert 'W: unable-to-read-zip' in out
    # there is a zip with no crc errors
    assert 'bad-crc-in-zip' not in out
    # there is zip with only 0 size files, which is not "uncompressed"
    assert 'uncompressed-zip' not in out


@pytest.mark.parametrize('package', ['binary/texlive-codepage-doc'])
def test_zip2(tmpdir, package, zipcheck):
    output, test = zipcheck
    test.check(get_tested_package(package, tmpdir))
    out = output.print_results(output.results)
    assert 'W: unable-to-read-zip' in out
