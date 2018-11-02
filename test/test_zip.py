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


@pytest.mark.parametrize('package', ['binary/asm'])
def test_jarfile(tmpdir, package, zipcheck):
    output, test = zipcheck
    test.check(get_tested_package(package, tmpdir))
    out = output.print_results(output.results)
    assert 'class-path-in-manifest' in out
    assert 'jar contains a hardcoded Class-Path' in out


@pytest.mark.parametrize('package', ['binary/ruby2.5-rubygem-rubyzip-testsuite'])
def test_zip1(tmpdir, package, zipcheck):
    output, test = zipcheck
    test.check(get_tested_package(package, tmpdir))
    out = output.print_results(output.results)
    # these are PW protected not broken so do not error about them
    assert 'W: unable-to-read-zip' in out
    # there is zip with only 0 size files, which is not "uncompressed"
    assert 'uncompressed-zip' not in out


@pytest.mark.parametrize('package', ['binary/texlive-codepage-doc'])
def test_zip2(tmpdir, package, zipcheck):
    output, test = zipcheck
    test.check(get_tested_package(package, tmpdir))
    out = output.print_results(output.results)
    assert 'W: unable-to-read-zip' in out
