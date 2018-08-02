import os

import pytest
from rpmlint.Filter import Filter
from rpmlint.RpmFileCheck import RpmFileCheck

from Testing import CONFIG, get_tested_package


@pytest.mark.parametrize('package', ['apache-commons-collections-testframework-javadoc'])
def test_distribution_tags(package):
    CONFIG.info = True
    output = Filter(CONFIG)
    test = RpmFileCheck(CONFIG, output)
    test.check(get_tested_package(os.path.join('binary', package)))
    out = output.print_results(output.results)
    assert 'filename-too-long-for-joliet' in out
    assert 'filename is too long to fit on a joliet filesystem' in out
