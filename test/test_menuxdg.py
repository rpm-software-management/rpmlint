import pytest
from rpmlint.checks.MenuXDGCheck import MenuXDGCheck
from rpmlint.filter import Filter

from Testing import CONFIG, get_tested_package, HAS_DESKTOP_FILE_UTILS


@pytest.fixture(scope='function', autouse=True)
def menuxdgcheck():
    CONFIG.info = True
    output = Filter(CONFIG)
    test = MenuXDGCheck(CONFIG, output)
    return output, test


@pytest.mark.skipif(not HAS_DESKTOP_FILE_UTILS, reason='Optional dependency desktop-file-utils not installed')
@pytest.mark.parametrize('package', ['binary/menuxdg1'])
def test_raises_parse_error(tmp_path, package, menuxdgcheck):
    output, test = menuxdgcheck
    test.check(get_tested_package(package, tmp_path))
    assert len(output.results) == 4
    out = output.print_results(output.results)
    assert 'contains parsing error' in out
    assert ' invalid-desktopfile ' in out
    assert 'check with desktop-file-validate' in out


@pytest.mark.skipif(not HAS_DESKTOP_FILE_UTILS, reason='Optional dependency desktop-file-utils not installed')
@pytest.mark.parametrize('package', ['binary/desktopfile-bad-binary'])
def test_without_binary(tmp_path, package, menuxdgcheck):
    output, test = menuxdgcheck
    test.check(get_tested_package(package, tmp_path))
    out = output.print_results(output.results)
    assert 'desktopfile-without-binary' in out


@pytest.mark.skipif(not HAS_DESKTOP_FILE_UTILS, reason='Optional dependency desktop-file-utils not installed')
@pytest.mark.parametrize('package', ['binary/desktopfile-bad-duplicate'])
def test_duplicate(tmp_path, package, menuxdgcheck):
    output, test = menuxdgcheck
    test.check(get_tested_package(package, tmp_path))
    out = output.print_results(output.results)
    assert 'desktopfile-duplicate-section' in out
    assert 'invalid-desktopfile' in out


@pytest.mark.skipif(not HAS_DESKTOP_FILE_UTILS, reason='Optional dependency desktop-file-utils not installed')
@pytest.mark.parametrize('package', ['binary/desktopfile-bad-section'])
def test_missing_header(tmp_path, package, menuxdgcheck):
    output, test = menuxdgcheck
    test.check(get_tested_package(package, tmp_path))
    out = output.print_results(output.results)
    assert 'desktopfile-missing-header' in out
    assert 'invalid-desktopfile' in out


@pytest.mark.skipif(not HAS_DESKTOP_FILE_UTILS, reason='Optional dependency desktop-file-utils not installed')
@pytest.mark.parametrize('package', ['binary/desktopfile-bad-unicode'])
def test_bad_unicode(tmp_path, package, menuxdgcheck):
    output, test = menuxdgcheck
    test.check(get_tested_package(package, tmp_path))
    out = output.print_results(output.results)
    assert 'non-utf8-desktopfile' in out


@pytest.mark.skipif(not HAS_DESKTOP_FILE_UTILS, reason='Optional dependency desktop-file-utils not installed')
@pytest.mark.parametrize('package', ['binary/desktopfile-good'])
def test_good(tmp_path, package, menuxdgcheck):
    output, test = menuxdgcheck
    test.check(get_tested_package(package, tmp_path))
    out = output.print_results(output.results)
    assert not out
