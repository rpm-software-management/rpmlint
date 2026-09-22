from mockdata.mock_alternatives import (
    AlternativeConfFolder,
    LibalternativesBorkedPackage,
    LibalternativesOkPackage,
    NonAlternativesPackage,
    UpdateAlternativesBorkedPackage,
    UpdateAlternativesCorrectnessPackage,
    UpdateAlternativesOkPackage,
)
import pytest
from rpmlint.checks.AlternativesCheck import AlternativesCheck
from rpmlint.filter import Filter

from Testing import CONFIG


@pytest.fixture(scope='function', autouse=True)
def alternativescheck():
    CONFIG.info = True
    output = Filter(CONFIG)
    test = AlternativesCheck(CONFIG, output)
    return output, test


#
# udpate-alternatives tests
#


@pytest.mark.parametrize('package', [UpdateAlternativesOkPackage])
def test_update_alternative_ok(package, alternativescheck):
    output, test = alternativescheck
    test.check(package)
    out = output.print_results(output.results)
    assert 'I: package-supports-update-alternatives' in out
    assert 'E' not in out
    assert 'W' not in out


@pytest.mark.parametrize('package', [UpdateAlternativesBorkedPackage])
def test_update_alternative_borked(package, alternativescheck):
    output, test = alternativescheck
    test.check(package)
    out = output.print_results(output.results)
    assert 'E: update-alternatives-requirement-missing' in out
    assert 'E: alternative-generic-name-not-symlink' in out
    assert 'E: alternative-link-not-ghost' in out
    assert 'E: update-alternatives-postun-call-missing' in out


@pytest.mark.parametrize('package', [NonAlternativesPackage])
def test_non_update_alternative_pkg(package, alternativescheck):
    output, test = alternativescheck
    test.check(package)
    out = output.print_results(output.results)
    # here we just check if there is no requirements checking on
    # non update-alternatived package
    assert 'E' not in out
    assert 'W' not in out


@pytest.mark.parametrize('package', [UpdateAlternativesCorrectnessPackage])
def test_update_alternatives_correctness(package, alternativescheck):
    output, test = alternativescheck
    test.check(package)
    out = output.print_results(output.results)
    assert 'E: update-alternatives-postun-call-missing' not in out


#
# libalternatives tests
#


@pytest.mark.parametrize('package', [LibalternativesOkPackage])
def test_libalternative_ok(package, alternativescheck):
    output, test = alternativescheck
    test.check(package)
    out = output.print_results(output.results)
    assert 'I: package-supports-libalternatives' in out
    assert 'E' not in out
    assert 'W' not in out


@pytest.mark.parametrize('package', [LibalternativesBorkedPackage])
def test_libalternative_borked(package, alternativescheck):
    output, test = alternativescheck
    test.check(package)
    out = output.print_results(output.results)
    assert 'I: package-supports-libalternatives' in out
    assert 'I: libalternatives-conf-not-found' in out
    assert 'E: alts-requirement-missed' in out
    assert 'E: libalternatives-directory-not-exist' in out
    assert 'E: empty-libalternatives-directory' in out
    assert 'W: man-entry-value-not-found' in out
    assert 'W: binary-entry-value-not-found' in out


@pytest.mark.parametrize('package', [AlternativeConfFolder])
def test_alternative_conf_folder(package, alternativescheck):
    output, test = alternativescheck
    test.check(package)
    out = output.print_results(output.results)
    assert 'E: libalternatives-conf-not-found' not in out
    assert 'W: wrong-tag-found' in out
    assert 'E: wrong-entry-format' in out
    assert 'W: binary-entry-value-not-found' in out
