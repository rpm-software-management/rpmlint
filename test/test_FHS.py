from mockdata.mock_FHS import NoFHSPackage
import pytest
from rpmlint.checks.FHSCheck import FHSCheck
from rpmlint.filter import Filter

from Testing import CONFIG


@pytest.fixture(scope='function', autouse=True)
def fhscheck():
    CONFIG.info = True
    output = Filter(CONFIG)
    test = FHSCheck(CONFIG, output)
    return output, test


@pytest.mark.parametrize('package', [NoFHSPackage])
def test_FHS_compliance(package, fhscheck):
    """
    Check that the directories are not FHS compliant.
    """
    output, test = fhscheck
    test.check(package)
    out = output.print_results(output.results)

    # Check invalid /usr subdirectory
    assert 'non-standard-dir-in-usr' in out
    assert 'sbin' in out

    # Check invalid /var subdirectory
    assert 'non-standard-dir-in-var' in out
    assert 'lib' in out
