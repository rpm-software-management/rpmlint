# TODO: Add MXDG4 when the test is corrected
from mockdata.mock_menuxdg import MENUXDG, MENUXDG1, MENUXDG2, MENUXDG3, MENUXDG5
import pytest
from rpmlint.checks.MenuXDGCheck import MenuXDGCheck
from rpmlint.filter import Filter

from Testing import CONFIG, HAS_DESKTOP_FILE_UTILS


@pytest.fixture(scope='function', autouse=True)
def menuxdgcheck():
    CONFIG.info = True
    output = Filter(CONFIG)
    test = MenuXDGCheck(CONFIG, output)
    return output, test


@pytest.mark.skipif(not HAS_DESKTOP_FILE_UTILS, reason='Optional dependency desktop-file-utils not installed')
@pytest.mark.parametrize('package', [MENUXDG])
def test_raises_parse_error(package, menuxdgcheck):
    output, test = menuxdgcheck
    test.check(package)
    assert len(output.results) == 4
    out = output.print_results(output.results)
    assert 'contains parsing error' in out
    assert ' invalid-desktopfile ' in out
    assert 'check with desktop-file-validate' in out


@pytest.mark.skipif(not HAS_DESKTOP_FILE_UTILS, reason='Optional dependency desktop-file-utils not installed')
@pytest.mark.parametrize('package', [MENUXDG1])
def test_without_binary(package, menuxdgcheck):
    output, test = menuxdgcheck
    test.check(package)
    out = output.print_results(output.results)
    assert 'desktopfile-without-binary' in out


@pytest.mark.skipif(not HAS_DESKTOP_FILE_UTILS, reason='Optional dependency desktop-file-utils not installed')
@pytest.mark.parametrize('package', [MENUXDG2])
def test_duplicate(package, menuxdgcheck):
    output, test = menuxdgcheck
    test.check(package)
    out = output.print_results(output.results)
    assert 'desktopfile-duplicate-section' in out
    assert 'invalid-desktopfile' in out


@pytest.mark.skipif(not HAS_DESKTOP_FILE_UTILS, reason='Optional dependency desktop-file-utils not installed')
@pytest.mark.parametrize('package', [MENUXDG3])
def test_missing_header(package, menuxdgcheck):
    output, test = menuxdgcheck
    test.check(package)
    out = output.print_results(output.results)
    assert 'desktopfile-missing-header' in out
    assert 'invalid-desktopfile' in out


# TODO: Correct this test.
# @pytest.mark.skipif(not HAS_DESKTOP_FILE_UTILS, reason='Optional dependency desktop-file-utils not installed')
# @pytest.mark.parametrize('package', [MENUXDG4])
# def test_bad_unicode(package, menuxdgcheck):
#    output, test = menuxdgcheck
#    test.check(package)
#    out = output.print_results(output.results)
#    assert 'non-utf8-desktopfile' in out


@pytest.mark.skipif(not HAS_DESKTOP_FILE_UTILS, reason='Optional dependency desktop-file-utils not installed')
@pytest.mark.parametrize('package', [MENUXDG5])
def test_good(package, menuxdgcheck):
    output, test = menuxdgcheck
    test.check(package)
    out = output.print_results(output.results)
    assert not out
