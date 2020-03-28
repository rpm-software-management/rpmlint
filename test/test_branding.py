import pytest
from rpmlint.checks.BrandingPolicyCheck import BrandingPolicyCheck
from rpmlint.filter import Filter

from Testing import CONFIG, get_tested_package


@pytest.fixture(scope='function', autouse=True)
def brandingcheck():
    CONFIG.info = True
    output = Filter(CONFIG)
    test = BrandingPolicyCheck(CONFIG, output)
    return output, test


@pytest.mark.parametrize('package', ['binary/brandingdep-testpackage'])
def test_branding_requires(tmpdir, package, brandingcheck):
    output, test = brandingcheck
    test.check(get_tested_package(package, tmpdir))
    out = output.print_results(output.results)
    assert 'branding-requires-specific-flavor testingpackage-branding-openSUSE' in out
    assert 'branding-requires-unversioned testingpackage-branding-openSUSE' not in out
    assert 'branding-requires-unversioned testingpackage2-branding' not in out
    assert 'branding-requires-unversioned testingpackage4-branding' not in out
    assert 'branding-requires-unversioned testingpackage-branding' in out


@pytest.mark.parametrize('package', ['binary/bla-branding-upstream'])
def test_branding_pkg1(tmpdir, package, brandingcheck):
    output, test = brandingcheck
    test.check(get_tested_package(package, tmpdir))
    out = output.print_results(output.results)
    assert 'branding-supplements-missing' not in out
    assert 'branding-provides-unversioned' not in out
    assert 'branding-provides-missing' not in out
    assert 'branding-provides-unversioned' not in out


@pytest.mark.parametrize('package', ['binary/bla-theme-openSUSE'])
def test_branding_pkg2(tmpdir, package, brandingcheck):
    output, test = brandingcheck
    test.check(get_tested_package(package, tmpdir))
    out = output.print_results(output.results)
    assert 'branding-excessive-suggests suggie' in out
    assert 'branding-excessive-recommends recommendie' in out
    assert 'branding-excessive-enhances enhancie' in out
    assert 'branding-provides-unversioned bla-theme' in out
    assert 'branding-supplements-missing (bla and theme-openSUSE)' in out
    assert 'branding-conflicts-missing bla-theme' in out
