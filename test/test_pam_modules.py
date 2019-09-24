import pytest
from rpmlint.checks.PAMModulesCheck import PAMModulesCheck
from rpmlint.filter import Filter

from Testing import CONFIG, get_tested_package


@pytest.fixture(scope='function', autouse=True)
def pammodulecheck():
    CONFIG.info = True
    output = Filter(CONFIG)
    test = PAMModulesCheck(CONFIG, output)
    return output, test


@pytest.mark.parametrize('package', ['binary/pam-module'])
def test_pam_modules(tmpdir, package, pammodulecheck):
    output, test = pammodulecheck
    test.check(get_tested_package(package, tmpdir))
    out = output.print_results(output.results)
    assert 'E: pam-unauthorized-module pam-module.so' in out
