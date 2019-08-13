from unittest.mock import patch

import pytest
from rpmlint.checks.AppDataCheck import AppDataCheck
from rpmlint.filter import Filter

from Testing import CONFIG, get_tested_package


@pytest.fixture(scope='function', autouse=True)
def appdatacheck():
    CONFIG.info = True
    output = Filter(CONFIG)
    test = AppDataCheck(CONFIG, output)
    return output, test


@pytest.mark.parametrize('package', ['binary/appdata'])
def test_appdata_fail(tmpdir, package, appdatacheck):
    output, test = appdatacheck
    test.check(get_tested_package(package, tmpdir))
    out = output.print_results(output.results)
    # there are two borked packages
    assert len(output.results) == 2
    assert 'invalid-appdata-file' in out


@pytest.mark.parametrize('package', ['binary/appdata'])
@patch('rpmlint.checks.AppDataCheck.AppDataCheck.cmd', 'command-really-not-found')
def test_appdata_fail_no_checker(tmpdir, package, appdatacheck):
    output, test = appdatacheck
    test.check(get_tested_package(package, tmpdir))
    out = output.print_results(output.results)
    # there is just one borked file as the other is invalid content
    # but valid xml
    assert len(output.results) == 1
    assert 'invalid-appdata-file' in out
