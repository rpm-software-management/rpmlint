import os

import pytest
from rpmlint import TagsCheck

from Testing import getTestedPackage


@pytest.mark.parametrize('package', ['unexpanded1'])
def test_unexpanded_macros(capsys, package):
    TagsCheck.check.check(getTestedPackage(os.path.join('binary', package)))
    out, err = capsys.readouterr()
    assert 'unexpanded-macro Recommends' in out
    assert 'unexpanded-macro Provides' in out
    assert 'unexpanded-macro Conflicts' in out
    assert 'unexpanded-macro Suggests' in out
    assert 'unexpanded-macro Obsoletes' in out
    assert 'unexpanded-macro Enhances' in out
