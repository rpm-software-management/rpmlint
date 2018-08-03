import pytest
from rpmlint.checks.DistributionCheck import DistributionCheck
from rpmlint.Filter import Filter

from Testing import CONFIG, get_tested_package


@pytest.fixture(scope='function', autouse=True)
def distributioncheck():
    CONFIG.info = True
    output = Filter(CONFIG)
    test = DistributionCheck(CONFIG, output)
    return output, test


@pytest.mark.parametrize('package', ['binary/ngircd'])
def test_distribution_tags(tmpdir, package):
    output, test = distributioncheck()
    test.check(get_tested_package(package, tmpdir))
    assert len(output.results) == 2
    out = output.print_results(output.results)
    assert 'manpage-not-compressed' in out
    assert 'invalid-distribution' not in out
    assert 'invalid-vendor' not in out
    assert 'This manual page is not compressed with the bz2 compression' in out
