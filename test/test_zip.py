import os

import pytest
from rpmlint.Filter import Filter
from rpmlint.ZipCheck import ZipCheck

from Testing import CONFIG, getTestedPackage


@pytest.mark.parametrize('package', ['asm'])
def test_jarfile(package):
    CONFIG.info = True
    output = Filter(CONFIG)
    test = ZipCheck(CONFIG, output)
    test.check(getTestedPackage(os.path.join('binary', package)))
    out = output.print_results(output.results)
    assert 'class-path-in-manifest' in out
    assert 'jar contains a hardcoded Class-Path' in out


@pytest.mark.parametrize('package', ['ruby2.5-rubygem-rubyzip-testsuite'])
def test_zip1(package):
    CONFIG.info = True
    output = Filter(CONFIG)
    test = ZipCheck(CONFIG, output)
    test.check(getTestedPackage(os.path.join('binary', package)))
    out = output.print_results(output.results)
    # these are PW protected not broken so do not error about them
    assert 'W: unable-to-read-zip' in out
    # there is zip with only 0 size files, which is not "uncompressed"
    assert 'uncompressed-zip' not in out


@pytest.mark.parametrize('package', ['texlive-codepage-doc'])
def test_zip2(package):
    CONFIG.info = True
    output = Filter(CONFIG)
    test = ZipCheck(CONFIG, output)
    test.check(getTestedPackage(os.path.join('binary', package)))
    out = output.print_results(output.results)
    assert 'W: unable-to-read-zip' in out
