import pytest
from rpmlint.checks.SharedLibraryPolicyCheck import SharedLibraryPolicyCheck
from rpmlint.filter import Filter

from Testing import CONFIG, get_tested_package


@pytest.fixture(scope='function', autouse=True)
def slpcheck():
    CONFIG.info = True
    output = Filter(CONFIG)
    test = SharedLibraryPolicyCheck(CONFIG, output)
    return output, test


@pytest.mark.parametrize('package', ['binary/libtest1'])
def test_shlib_policy_wrong_name(tmpdir, package, slpcheck):
    output, test = slpcheck
    test.check(get_tested_package(package, tmpdir))
    out = output.print_results(output.results)
    assert 'W: shlib-unversioned-lib libtest.so.1x' in out


@pytest.mark.parametrize('package', ['binary/libslp-missing-suffix'])
def test_shlib_policy_missing_suffix(tmpdir, package, slpcheck):
    output, test = slpcheck
    test.check(get_tested_package(package, tmpdir))
    out = output.print_results(output.results)
    assert 'E: shlib-policy-excessive-dependency libsparta.so.2' in out


@pytest.mark.parametrize('package', ['binary/libslp1234'])
def test_shlib_policy_errors(tmpdir, package, slpcheck):
    output, test = slpcheck
    test.check(get_tested_package(package, tmpdir))
    out = output.print_results(output.results)
    assert 'W: shlib-fixed-dependency libsparta.so.2 = 1.23' in out
