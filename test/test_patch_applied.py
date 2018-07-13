import os

import pytest
from rpmlint import SpecCheck

from Testing import getTestedSpecPackage


@pytest.mark.parametrize('package', ['SpecCheck2', 'SpecCheck3'])
def test_patch_not_applied(capsys, package):
    pkg = getTestedSpecPackage(os.path.join('spec', package))
    SpecCheck.check.check_spec(pkg, pkg.name)
    out, err = capsys.readouterr()
    assert 'patch-not-applied' not in out
