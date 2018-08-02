import os

import pytest
from rpmlint.DistributionCheck import DistributionCheck
from rpmlint.Filter import Filter

from Testing import CONFIG, get_tested_package


@pytest.mark.parametrize('package', ['ngircd'])
def test_distribution_tags(package):
    CONFIG.info = True
    output = Filter(CONFIG)
    test = DistributionCheck(CONFIG, output)
    test.check(get_tested_package(os.path.join('binary', package)))
    assert len(output.results) == 2
    out = output.print_results(output.results)
    assert 'manpage-not-compressed' in out
    assert 'invalid-distribution' not in out
    assert 'invalid-vendor' not in out
    assert 'This manual page is not compressed with the bz2 compression' in out
