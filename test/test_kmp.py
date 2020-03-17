import pytest
from rpmlint.checks.KMPPolicyCheck import KMPPolicyCheck
from rpmlint.filter import Filter

from Testing import CONFIG, get_tested_package


@pytest.fixture(scope='function', autouse=True)
def kmpcheck():
    CONFIG.info = True
    output = Filter(CONFIG)
    test = KMPPolicyCheck(CONFIG, output)
    return output, test


@pytest.mark.parametrize('package', ['binary/noreq-kmp-default'])
def test_kmp_noreq(tmpdir, package, kmpcheck):
    output, test = kmpcheck
    test.check(get_tested_package(package, tmpdir))
    out = output.print_results(output.results)
    assert 'kmp-missing-supplements' in out
    assert 'kmp-missing-requires' in out
    assert 'kmp-missing-enhances' in out


@pytest.mark.parametrize('package', ['binary/exces-enhances-kmp-default'])
def test_kmp_enhances(tmpdir, package, kmpcheck):
    output, test = kmpcheck
    test.check(get_tested_package(package, tmpdir))
    out = output.print_results(output.results)
    assert 'kmp-missing-supplements' in out
    assert 'kmp-missing-requires' not in out
    assert 'kmp-missing-enhances' not in out
    assert 'kmp-excessive-enhances' in out


@pytest.mark.parametrize('package', ['binary/supplements-kmp-default'])
def test_kmp_supplements(tmpdir, package, kmpcheck):
    output, test = kmpcheck
    test.check(get_tested_package(package, tmpdir))
    out = output.print_results(output.results)
    assert 'kmp-missing-supplements' not in out
    assert 'kmp-missing-requires' not in out
    assert 'kmp-missing-enhances' not in out
    assert 'kmp-excessive-enhances' not in out
    assert 'kmp-excessive-supplements' not in out
