import pytest
from rpmlint.checks.XinetdDepCheck import XinetdDepCheck
from rpmlint.filter import Filter

from Testing import CONFIG, get_tested_package


@pytest.fixture(scope='function', autouse=True)
def xinetdcheck():
    CONFIG.info = True
    output = Filter(CONFIG)
    test = XinetdDepCheck(CONFIG, output)
    return output, test


@pytest.mark.parametrize('package', ['binary/needxinetd'])
def test_xinetd(tmpdir, package, xinetdcheck):
    output, test = xinetdcheck
    test.check(get_tested_package(package, tmpdir))
    out = output.print_results(output.results)
    assert 'E: obsolete-xinetd-requirement' in out
