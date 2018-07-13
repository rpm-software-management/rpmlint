import os

import pytest
from rpmlint import DistributionCheck

from Testing import getTestedPackage


@pytest.mark.parametrize('package', ['ngircd'])
def test_distribution_tags(capsys, package):
    DistributionCheck.check.check(getTestedPackage(os.path.join('binary', package)))
    out, err = capsys.readouterr()
    assert 'invalid-distribution' not in out
    assert 'invalid-vendor' not in out
