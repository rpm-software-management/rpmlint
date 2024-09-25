from mockdata.mock_shlib_policy import (
    LibslpMissingSuffixPackage,
    Libslp1234Package,
    Libtest1Package,
)
import pytest
from rpmlint.checks.SharedLibraryPolicyCheck import SharedLibraryPolicyCheck
from rpmlint.filter import Filter

from Testing import CONFIG


@pytest.fixture(scope='function', autouse=True)
def slpcheck():
    CONFIG.info = True
    output = Filter(CONFIG)
    test = SharedLibraryPolicyCheck(CONFIG, output)
    return output, test


@pytest.mark.parametrize('package', [Libtest1Package])
def test_shlib_policy_wrong_name(package, slpcheck):
    output, test = slpcheck
    test.check(package)
    out = output.print_results(output.results)
    assert 'W: shlib-unversioned-lib libtest.so.1x' in out


@pytest.mark.parametrize('package', [LibslpMissingSuffixPackage])
def test_shlib_policy_missing_suffix(package, slpcheck):
    output, test = slpcheck
    test.check(package)
    out = output.print_results(output.results)
    assert 'E: shlib-policy-excessive-dependency libsparta.so.2' in out


@pytest.mark.parametrize('package', [Libslp1234Package])
def test_shlib_policy_errors(package, slpcheck):
    output, test = slpcheck
    test.check(package)
    out = output.print_results(output.results)
    assert 'W: shlib-fixed-dependency libsparta.so.2 = 1.23' in out
