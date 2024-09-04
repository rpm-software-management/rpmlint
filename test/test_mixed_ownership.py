from mockdata.mock_mixed_ownership import MixedOwnership
import pytest
from rpmlint.checks.MixedOwnershipCheck import MixedOwnershipCheck
from rpmlint.filter import Filter

from Testing import CONFIG


@pytest.fixture(scope='function', autouse=True)
def mixedownershipcheck():
    CONFIG.info = True
    output = Filter(CONFIG)
    test = MixedOwnershipCheck(CONFIG, output)
    return output, test


@pytest.mark.parametrize('package', [MixedOwnership])
def test_mixed_ownership(package, mixedownershipcheck):
    output, test = mixedownershipcheck
    test.check(package)
    out = output.print_results(output.results)
    assert 'noproblem' not in out
    assert 'file-parent-ownership-mismatch Path "/var/lib/badfolder/broken1" owned by "root" is stored in directory owned by "nobody"' in out
    assert 'file-parent-ownership-mismatch Path "/var/lib/badfolder/correctperms" owned by "root" is stored in directory owned by "nobody"' in out
