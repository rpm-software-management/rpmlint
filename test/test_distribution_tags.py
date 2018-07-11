import os
import re

import pytest
from rpmlint import SpecCheck

from Testing import getTestedSpecPackage


@pytest.mark.parametrize('package', ['SpecCheck'])
def test_distribution_tags(capsys, package):
    pkg = getTestedSpecPackage(os.path.join('spec', package))
    SpecCheck.check.check_spec(pkg, pkg.name)
    out, err = capsys.readouterr()
    assert 'patch-not-applied Patch3' in out
    assert not re.search(r'patch-not-applied Patch\b', out)
    assert not re.search('patch-not-applied Patch[0124567]', out)
    assert 'libdir-macro-in-noarch-package' not in out
    assert len(re.findall("macro-in-comment", out)) == 1
    assert 'unversioned-explicit-provides unversioned-provides' in out
    assert 'unversioned-explicit-provides versioned-provides' not in out
    assert 'unversioned-explicit-provides /' not in out
    assert 'unversioned-explicit-obsoletes unversioned-obsoletes' in out
    assert 'unversioned-explicit-obsoletes versioned-obsoletes' not in out
    assert 'unversioned-explicit-obsoletes /' not in out
    assert 'setup-not-quiet' in out
