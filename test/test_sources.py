import os

import pytest
from rpmlint.Filter import Filter
from rpmlint.SourceCheck import SourceCheck

from Testing import CONFIG, get_tested_package


@pytest.mark.parametrize('package', ['wrongsrc'])
def test_inconsistent_file_extension(package):
    CONFIG.info = True
    output = Filter(CONFIG)
    test = SourceCheck(CONFIG, output)
    test.check(get_tested_package(os.path.join('source', package)))
    assert len(output.results) == 3
    out = output.print_results(output.results)
    assert 'inconsistent-file-extension' in out
    assert 'a file should have' in out
