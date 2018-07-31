import os

import pytest
from rpmlint.Filter import Filter
from rpmlint.TagsCheck import TagsCheck

from Testing import CONFIG, getTestedPackage


@pytest.mark.parametrize('package', ['unexpanded1'])
def test_unexpanded_macros(package):
    CONFIG.info = True
    output = Filter(CONFIG)
    test = TagsCheck(CONFIG, output)
    test.check(getTestedPackage(os.path.join('binary', package)))
    out = output.print_results(output.results)
    assert 'unexpanded-macro Recommends' in out
    assert 'unexpanded-macro Provides' in out
    assert 'unexpanded-macro Conflicts' in out
    assert 'unexpanded-macro Suggests' in out
    assert 'unexpanded-macro Obsoletes' in out
    assert 'unexpanded-macro Enhances' in out
