import pytest
from rpmlint.checks.TagsCheck import TagsCheck
from rpmlint.filter import Filter

from Testing import CONFIG, get_tested_package


@pytest.fixture(scope='function', autouse=True)
def tagscheck():
    CONFIG.info = True
    output = Filter(CONFIG)
    test = TagsCheck(CONFIG, output)
    return output, test


@pytest.mark.parametrize('package', ['binary/unexpanded1'])
def test_unexpanded_macros(tmpdir, package, tagscheck):
    output, test = tagscheck
    test.check(get_tested_package(package, tmpdir))
    out = output.print_results(output.results)
    assert 'unexpanded-macro Recommends' in out
    assert 'unexpanded-macro Provides' in out
    assert 'unexpanded-macro Conflicts' in out
    assert 'unexpanded-macro Suggests' in out
    assert 'unexpanded-macro Obsoletes' in out
    assert 'unexpanded-macro Enhances' in out


@pytest.mark.parametrize('package', ['binary/self'])
def test_self_provides(tmpdir, package, tagscheck):
    output, test = tagscheck
    test.check(get_tested_package(package, tmpdir))
    out = output.print_results(output.results)
    assert 'E: useless-provides self' in out


@pytest.mark.parametrize('package', ['binary/foo-devel'])
def test_development_package(tmpdir, package, tagscheck):
    output, test = tagscheck
    test.check(get_tested_package(package, tmpdir))
    out = output.print_results(output.results)
    assert 'W: devel-package-with-non-devel-group Games' in out


@pytest.mark.parametrize('package', ['binary/missingprovides'])
def test_missing_provides(tmpdir, package, tagscheck):
    output, test = tagscheck
    test.check(get_tested_package(package, tmpdir))
    out = output.print_results(output.results)
    assert 'E: no-pkg-config-provides' in out


@pytest.mark.parametrize('package', ['binary/invalid-exception'])
def test_invalid_license_exception(tmpdir, package, tagscheck):
    output, test = tagscheck
    test.check(get_tested_package(package, tmpdir))
    out = output.print_results(output.results)
    assert 'W: invalid-license-exception sparta' in out


@pytest.mark.parametrize('package', ['binary/valid-exception'])
def test_valid_license_exception(tmpdir, package, tagscheck):
    CONFIG.info = True
    CONFIG.configuration['ValidLicenseExceptions'] = ['389-exception']
    output = Filter(CONFIG)
    test = TagsCheck(CONFIG, output)
    test.check(get_tested_package(package, tmpdir))
    out = output.print_results(output.results)
    assert 'W: invalid-license-exception' not in out
