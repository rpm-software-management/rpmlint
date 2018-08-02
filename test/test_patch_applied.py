import os

import pytest
from rpmlint.Filter import Filter
from rpmlint.SpecCheck import SpecCheck

from Testing import CONFIG, get_tested_spec_package


@pytest.mark.parametrize('package', ['SpecCheck2', 'SpecCheck3'])
def test_patch_not_applied(package):
    pkg = get_tested_spec_package(os.path.join('spec', package))
    CONFIG.info = True
    output = Filter(CONFIG)
    test = SpecCheck(CONFIG, output)
    test.check_spec(pkg, pkg.name)
    out = output.print_results(output.results)
    assert 'patch-not-applied' not in out
