from unittest.mock import patch

from mockdata.mock_appdata import APPDATA, APPDATA2
import pytest
from rpmlint.checks.AppDataCheck import AppDataCheck
from rpmlint.filter import Filter

from Testing import CONFIG, HAS_APPSTREAM_GLIB


@pytest.fixture(scope='function', autouse=True)
def appdatacheck():
    CONFIG.info = True
    output = Filter(CONFIG)
    test = AppDataCheck(CONFIG, output)
    return output, test


@pytest.mark.skipif(not HAS_APPSTREAM_GLIB, reason='Optional dependency appstream-glib not installed')
@pytest.mark.parametrize('package', [APPDATA])
def test_appdata_fail(package, appdatacheck):
    output, test = appdatacheck
    test.check(package)
    out = output.print_results(output.results)
    # there are two borked packages
    assert len(output.results) == 2
    assert 'invalid-appdata-file' in out


@pytest.mark.parametrize('package', [APPDATA2])
@patch('rpmlint.checks.AppDataCheck.AppDataCheck.cmd', 'command-really-not-found')
def test_appdata_fail_no_checker(package, appdatacheck):
    output, test = appdatacheck
    test.check(package)
    out = output.print_results(output.results)
    # there is just one borked file as the other is invalid content
    # but valid xml
    assert len(output.results) == 1
    assert 'invalid-appdata-file' in out
