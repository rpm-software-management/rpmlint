from mockdata.mock_pam_modules import PAMMODULES
import pytest
from rpmlint.checks.PAMModulesCheck import PAMModulesCheck
from rpmlint.filter import Filter

from Testing import CONFIG


@pytest.fixture(scope='function', autouse=True)
def pammodulecheck():
    CONFIG.info = True
    output = Filter(CONFIG)
    test = PAMModulesCheck(CONFIG, output)
    return output, test


@pytest.mark.parametrize('package', [PAMMODULES])
def test_pam_modules(package, pammodulecheck):
    output, test = pammodulecheck
    test.check(package)
    out = output.print_results(output.results)
    assert 'E: pam-unauthorized-module pam-module.so' in out
