import os

import pytest
from rpmlint import PamCheck

from Testing import getTestedPackage


@pytest.mark.parametrize('package', ['PamCheck'])
def test_pam_check(capsys, package):
    PamCheck.check.check(getTestedPackage(os.path.join('binary', package)))
    out, err = capsys.readouterr()
    assert 'PamCheck.i586: E: use-old-pam-stack' in out
    assert '/etc/pam.d/PamCheck (line 1)' in out
