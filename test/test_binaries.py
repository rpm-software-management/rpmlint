import os

import pytest
from rpmlint.BinariesCheck import BinariesCheck
from rpmlint.Filter import Filter

from Testing import CONFIG, getTestedPackage


@pytest.mark.parametrize('package', ['cyrus-imapd', 'dovecot'])
def test_forbidden_c_calls(package):
    output = Filter(CONFIG)
    test = BinariesCheck(CONFIG, output)
    test.check(getTestedPackage(os.path.join('binary', package)))
    assert 'crypto-policy-non-compliance' in output.print_results(output.results)


@pytest.mark.parametrize('package', ['ngircd'])
def test_waived_forbidden_c_calls(package):
    CONFIG.info = True
    output = Filter(CONFIG)
    test = BinariesCheck(CONFIG, output)
    test.check(getTestedPackage(os.path.join('binary', package)))
    # there are 3 warnings/etc
    assert len(output.results) == 3
    # assert the details are properly printed to the content
    assert len(output.print_results(output.results).splitlines()) == 13
    assert 'crypto-policy-non-compliance' not in output.print_results(output.results)
