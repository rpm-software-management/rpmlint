import pytest
from rpmlint.checks.PolkitDefaultPrivsAllowlist import PolkitActionsCheck, PolkitDefaultPrivsOverrideCheck
from rpmlint.filter import Filter

from Testing import CONFIG, get_tested_package


@pytest.fixture(scope='function', autouse=True)
def polkit_default_privs_override_check(tmpdir):
    CONFIG.info = True
    output = Filter(CONFIG)
    test = PolkitDefaultPrivsOverrideCheck(CONFIG, output)
    return output, test


@pytest.mark.parametrize('package', ['binary/polkit-def-privs-test'])
def test_polkit_perm_files(tmpdir, package, polkit_default_privs_override_check):
    output, test = polkit_default_privs_override_check
    test.check(get_tested_package(package, tmpdir))
    out = output.print_results(output.results)
    assert 'noproblem' not in out
    assert 'polkit-unauthorized-file /etc/polkit-default-privs.d/foo.standard' in out
    assert 'polkit-ghost-file /etc/polkit-default-privs.d/ghost' in out


@pytest.fixture(scope='function', autouse=True)
def polkit_actions_check(tmpdir):
    CONFIG.info = True
    output = Filter(CONFIG)
    test = PolkitActionsCheck(CONFIG, output)
    return output, test


@pytest.mark.parametrize('package', ['binary/polkit-0'])
def test_polkit_actions(tmpdir, package, polkit_actions_check):
    output, test = polkit_actions_check
    test.check(get_tested_package(package, tmpdir))
    out = output.print_results(output.results)
    assert 'noproblem' not in out
    assert 'polkit-cant-acquire-privilege org.opensuse.test.bar (no:auth_admin:auth_admin)' in out
    assert 'polkit-unauthorized-privilege org.opensuse.test.baz (auth_admin:auth_admin:auth_self)' in out
    assert 'polkit-unauthorized-privilege org.opensuse.test.baz2 (auth_admin:auth_admin:yes)' in out
    assert 'polkit-untracked-privilege org.opensuse.test.bar (no:auth_admin:auth_admin)' in out
    assert 'polkit-untracked-privilege org.opensuse.test.foo (auth_admin:auth_admin:auth_admin)' in out
