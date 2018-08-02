import re

import pytest
from rpmlint.Filter import Filter
from rpmlint.SpecCheck import SpecCheck

from Testing import CONFIG, get_tested_spec_package


@pytest.mark.parametrize('package', ['spec/SpecCheck'])
def test_distribution_tags(package):
    pkg = get_tested_spec_package(package)
    CONFIG.info = True
    output = Filter(CONFIG)
    test = SpecCheck(CONFIG, output)
    test.check_spec(pkg, pkg.name)
    out = output.print_results(output.results)
    assert 'patch-not-applied Patch3' in out
    assert not re.search(r'patch-not-applied Patch\b', out)
    assert not re.search('patch-not-applied Patch[0124567]', out)
    assert 'libdir-macro-in-noarch-package' not in out
    assert len(re.findall('macro-in-comment', out)) == 1
    assert 'unversioned-explicit-provides unversioned-provides' in out
    assert 'unversioned-explicit-provides versioned-provides' not in out
    assert 'unversioned-explicit-provides /' not in out
    assert 'unversioned-explicit-obsoletes unversioned-obsoletes' in out
    assert 'unversioned-explicit-obsoletes versioned-obsoletes' not in out
    assert 'unversioned-explicit-obsoletes /' not in out
    assert 'setup-not-quiet' in out
