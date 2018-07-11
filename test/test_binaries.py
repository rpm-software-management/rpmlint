import os

import pytest
from rpmlint import BinariesCheck

from Testing import getTestedPackage


@pytest.mark.parametrize('package', ['cyrus-imapd', 'dovecot'])
def test_forbidden_c_calls(capsys, package):
    BinariesCheck.check.check(getTestedPackage(os.path.join('binary', package)))
    out, err = capsys.readouterr()
    assert 'crypto-policy-non-compliance' in out


@pytest.mark.parametrize('package', ['ngircd'])
def test_waived_forbidden_c_calls(capsys, package):
    BinariesCheck.check.check(getTestedPackage(os.path.join('binary', package)))
    out, err = capsys.readouterr()
    assert 'crypto-policy-non-compliance' not in out
