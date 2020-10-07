import os
import os.path

import pytest
from rpmlint.checks.PolkitRulesAllowedCheck import PolkitRulesAllowedCheck
from rpmlint.filter import Filter
import toml

from Testing import CONFIG, get_tested_package


@pytest.fixture(scope='function', autouse=True)
def polkit_rules_allowed_check(tmpdir):
    CONFIG.info = True

    # make the check search for its allow list in 'tmpdir'
    CONFIG.configuration['WhitelistDataDir'] = [tmpdir]
    CONFIG.configuration['PolkitRulesWhitelist'] = ('allowed-polkit-rules.toml',)

    output = Filter(CONFIG)
    test = PolkitRulesAllowedCheck(CONFIG, output)

    # make an empty allow list
    with open(os.path.join(tmpdir, 'allowed-polkit-rules.toml'), 'w') as fd:
        toml.dump({'polkit-rules-test': {'bsc#0': {'digests': {
            '/usr/share/polkit-1/rules.d/regular': 'sha256:invalid'
        }}}}, fd)

    return output, test


@pytest.mark.parametrize('package', ['binary/polkit-rules-test'])
def test_polkit_privs(tmpdir, package, polkit_rules_allowed_check):
    output, test = polkit_rules_allowed_check
    test.check(get_tested_package(package, tmpdir))
    out = output.print_results(output.results)
    assert 'noproblem' not in out
    assert 'polkit-changed-rules /usr/share/polkit-1/rules.d/regular' in out
    assert 'polkit-unauthorized-rules /etc/polkit-1/rules.d/regular' in out
    assert 'polkit-ghost-file /usr/share/polkit-1/rules.d/ghost' in out
