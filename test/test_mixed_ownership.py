import pytest
from rpmlint.checks.MixedOwnershipCheck import MixedOwnershipCheck
from rpmlint.filter import Filter

from Testing import CONFIG, get_tested_mock_package


@pytest.fixture(scope='function', autouse=True)
def mixedownershipcheck():
    CONFIG.info = True
    output = Filter(CONFIG)
    test = MixedOwnershipCheck(CONFIG, output)
    return output, test


@pytest.mark.parametrize('package', [get_tested_mock_package(
files={
'/usr/bin/noproblem': {},
'/var/lib/badfolder': {'user': 'nobody'},
'/var/lib/badfolder/broken1': {'user': 'root'},
'/var/lib/badfolder/correctperms': {'user': 'root'},
'/var/lib/badfolder/correctperms/broken2': {}
}
)])
def test_mixed_ownership(package, mixedownershipcheck):
    output, test = mixedownershipcheck
    test.check(package)
    out = output.print_results(output.results)
    assert 'noproblem' not in out
    assert 'file-parent-ownership-mismatch Path "/var/lib/badfolder/broken1" owned by "root" is stored in directory owned by "nobody"' in out
    assert 'file-parent-ownership-mismatch Path "/var/lib/badfolder/correctperms" owned by "root" is stored in directory owned by "nobody"' in out
