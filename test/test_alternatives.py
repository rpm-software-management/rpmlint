import pytest
from rpmlint.checks.AlternativesCheck import AlternativesCheck
from rpmlint.filter import Filter

from Testing import CONFIG, get_tested_package


@pytest.fixture(scope='function', autouse=True)
def alternativescheck():
    CONFIG.info = True
    output = Filter(CONFIG)
    test = AlternativesCheck(CONFIG, output)
    return output, test


@pytest.mark.parametrize('package', ['binary/alternatives-ok'])
def test_alternative_ok(tmpdir, package, alternativescheck):
    output, test = alternativescheck
    test.check(get_tested_package(package, tmpdir))
    out = output.print_results(output.results)
    assert 'E' not in out
    assert 'W' not in out


@pytest.mark.parametrize('package', ['binary/alternatives-borked'])
def test_alternative_borked(tmpdir, package, alternativescheck):
    output, test = alternativescheck
    test.check(get_tested_package(package, tmpdir))
    out = output.print_results(output.results)
    assert 'E: update-alternatives-requirement-missing' in out
    assert 'E: alternative-generic-name-not-symlink' in out
    assert 'E: alternative-link-not-ghost' in out
    assert 'E: update-alternatives-postun-call-missing' in out


@pytest.mark.parametrize('package', ['binary/self'])
def test_non_alternative_pkg(tmpdir, package, alternativescheck):
    output, test = alternativescheck
    test.check(get_tested_package(package, tmpdir))
    out = output.print_results(output.results)
    # here we just check if there is no requirements checking on
    # non update-alternatived package
    assert 'E' not in out
    assert 'W' not in out
