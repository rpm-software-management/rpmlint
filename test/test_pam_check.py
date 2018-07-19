import os

import pytest
from rpmlint.Filter import Filter
from rpmlint.PamCheck import PamCheck

from Testing import CONFIG, getTestedPackage


@pytest.mark.parametrize('package', ['PamCheck'])
def test_pam_check(package):
    CONFIG.info = True
    output = Filter(CONFIG)
    test = PamCheck(CONFIG, output)
    test.check(getTestedPackage(os.path.join('binary', package)))
    assert len(output.results) == 1
    out = output.print_results(output.results)
    assert 'PamCheck.i586: E: use-old-pam-stack' in out
    assert '/etc/pam.d/PamCheck (line 1)' in out
    assert 'Update pam file' in out
