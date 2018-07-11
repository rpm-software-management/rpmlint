import os

import pytest
from rpmlint import MenuXDGCheck

from Testing import getTestedPackage


@pytest.mark.parametrize('package', ['menuxdg1'])
def test_raises_parse_error(capsys, package):
    MenuXDGCheck.check.check(getTestedPackage(os.path.join('binary', package)))
    out, err = capsys.readouterr()
    assert 'contains parsing error' in out
    assert ' invalid-desktopfile ' in out
