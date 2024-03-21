from mockdata.mock_xinetd import RequireXinetd
import pytest
from rpmlint.checks.XinetdDepCheck import XinetdDepCheck
from rpmlint.filter import Filter

from Testing import CONFIG


@pytest.fixture(scope='function', autouse=True)
def xinetdcheck():
    CONFIG.info = True
    output = Filter(CONFIG)
    test = XinetdDepCheck(CONFIG, output)
    return output, test


@pytest.mark.parametrize('package', [RequireXinetd])
def test_xinetd(package, xinetdcheck):
    output, test = xinetdcheck
    test.check(package)
    out = output.print_results(output.results)
    assert 'E: obsolete-xinetd-requirement' in out
