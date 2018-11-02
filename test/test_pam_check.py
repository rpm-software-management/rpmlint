import pytest
from rpmlint.checks.PamCheck import PamCheck
from rpmlint.filter import Filter

from Testing import CONFIG, get_tested_package


@pytest.fixture(scope='function', autouse=True)
def pamcheck():
    CONFIG.info = True
    output = Filter(CONFIG)
    test = PamCheck(CONFIG, output)
    return output, test


@pytest.mark.parametrize('package', ['binary/PamCheck'])
def test_pam_check(tmpdir, package, pamcheck):
    output, test = pamcheck
    test.check(get_tested_package(package, tmpdir))
    assert len(output.results) == 1
    out = output.print_results(output.results)
    assert 'PamCheck.i586: E: use-old-pam-stack' in out
    assert '/etc/pam.d/PamCheck (line 1)' in out
    assert 'Update pam file' in out
