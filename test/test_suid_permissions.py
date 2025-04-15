import os
import stat

import pytest
from rpmlint.checks.SUIDPermissionsCheck import SUIDPermissionsCheck
from rpmlint.filter import Filter

import Testing
from Testing import get_tested_mock_package
from Testing import get_tested_package, get_tested_path


def get_suid_permissions_check(config_path):
    from rpmlint.config import Config

    if not os.path.isabs(config_path):
        config_path = get_tested_path('configs', config_path)
    config = Config([config_path])
    config.info = True
    output = Filter(config)
    test = SUIDPermissionsCheck(config, output)
    return output, test


@pytest.fixture(scope='function', autouse=True)
def permissions_check_profile(permissions_check):
    output, test = permissions_check
    test._parse_profile(str(get_tested_path('configs/permissions.secure')))
    return output, test


@pytest.fixture(scope='function', autouse=True)
def permissions_check():
    return get_suid_permissions_check(Testing.TEST_CONFIG[0])


@pytest.mark.parametrize('package', ['binary/testsuidpermissionscheck'])
def test_permissions_symlink(tmp_path, package, permissions_check_profile):
    output, test = permissions_check_profile
    test.check(get_tested_package(package, tmp_path))
    out = output.print_results(output.results)
    assert 'testsuidpermissionscheck.x86_64: W: permissions-symlink /var/lib/testsuidpermissionscheck/test_permissions_symlink' in out


@pytest.mark.parametrize('package', ['binary/testsuidpermissionscheck'])
def test_permissions_dir_without_slash(tmp_path, package, permissions_check_profile):
    output, test = permissions_check_profile
    test.check(get_tested_package(package, tmp_path))
    out = output.print_results(output.results)
    assert 'testsuidpermissionscheck.x86_64: W: permissions-dir-without-slash /var/lib/testsuidpermissionscheck/test_permissions_dir_without_slash' in out


@pytest.mark.parametrize('package', ['binary/testsuidpermissionscheck'])
def test_permissions_incorrect(tmp_path, package, permissions_check_profile):
    output, test = permissions_check_profile
    test.check(get_tested_package(package, tmp_path))
    out = output.print_results(output.results)
    assert 'testsuidpermissionscheck.x86_64: E: permissions-incorrect /var/lib/testsuidpermissionscheck/test_permissions_incorrect has mode 0755 but should be 0600' in out


@pytest.mark.parametrize('package', ['binary/testsuidpermissionscheck'])
def test_permissions_incorrect_owner(tmp_path, package, permissions_check_profile):
    output, test = permissions_check_profile
    test.check(get_tested_package(package, tmp_path))
    out = output.print_results(output.results)
    assert 'testsuidpermissionscheck.x86_64: E: permissions-incorrect-owner /var/lib/testsuidpermissionscheck/test_permissions_incorrect_owner belongs to root:root but should be abc:root' in out


@pytest.mark.parametrize('package', ['binary/testsuidpermissionscheck'])
def test_permissions_fscaps(tmp_path, package, permissions_check):
    output, test = permissions_check
    test.check(get_tested_package(package, tmp_path))
    out = output.print_results(output.results)
    assert "testsuidpermissionscheck.x86_64: E: permissions-fscaps /var/lib/testsuidpermissionscheck/test_permissions_fscaps has fscaps 'cap_net_raw=ep'" in out


@pytest.mark.parametrize('package', ['binary/testsuidpermissionscheck'])
def test_permissions_file_setuid_bit(tmp_path, package, permissions_check):
    output, test = permissions_check
    test.check(get_tested_package(package, tmp_path))
    out = output.print_results(output.results)
    assert 'testsuidpermissionscheck.x86_64: E: permissions-file-setuid-bit /var/lib/testsuidpermissionscheck/test_non_position_independent_executable_and_suid is packaged with setuid/setgid bits (04755)' in out
    assert 'testsuidpermissionscheck.x86_64: E: permissions-file-setuid-bit /var/lib/testsuidpermissionscheck/test_permissions_file_setuid_bit is packaged with setuid/setgid bits (04755)' in out


@pytest.mark.parametrize('package', ['binary/testsuidpermissionscheck'])
def test_permissions_directory_setuid_bit(tmp_path, package, permissions_check):
    output, test = permissions_check
    test.check(get_tested_package(package, tmp_path))
    out = output.print_results(output.results)
    assert 'testsuidpermissionscheck.x86_64: E: permissions-directory-setuid-bit /var/lib/testsuidpermissionscheck/test_permissions_directory_setuid_bit is packaged with setuid/setgid bits (04755)' in out


@pytest.mark.parametrize('package', ['binary/permissions-no-postin'])
def test_permissions_missing_postin(tmp_path, package, permissions_check):
    output, test = permissions_check
    test.check(get_tested_package(package, tmp_path))
    out = output.print_results(output.results)
    assert 'permissions-no-postin.x86_64: E: permissions-missing-postin missing %set_permissions /var/lib/permissions-no-postin/test_permissions_directory_setuid_bit in %post' in out
    assert 'permissions-no-postin.x86_64: E: permissions-missing-postin missing %set_permissions /var/lib/permissions-no-postin/test_permissions_file_setuid_bit in %post' in out
    assert 'permissions-no-postin.x86_64: E: permissions-directory-setuid-bit /var/lib/permissions-no-postin/test_permissions_directory_setuid_bit is packaged with setuid/setgid bits (04755)' in out
    assert 'permissions-no-postin.x86_64: E: permissions-file-setuid-bit /var/lib/permissions-no-postin/test_permissions_file_setuid_bit is packaged with setuid/setgid bits (04755)' in out


@pytest.mark.parametrize('package', ['binary/testsuidpermissionscheck'])
def test_permissions_missing_verifyscript(tmp_path, package, permissions_check):
    output, test = permissions_check
    test.check(get_tested_package(package, tmp_path))
    out = output.print_results(output.results)
    assert 'testsuidpermissionscheck.x86_64: W: permissions-missing-verifyscript missing %verify_permissions -e /var/lib/testsuidpermissionscheck/test_non_position_independent_executable_and_suid' in out
    assert 'testsuidpermissionscheck.x86_64: W: permissions-missing-verifyscript missing %verify_permissions -e /var/lib/testsuidpermissionscheck/test_permissions_directory_setuid_bit' in out
    assert 'testsuidpermissionscheck.x86_64: W: permissions-missing-verifyscript missing %verify_permissions -e /var/lib/testsuidpermissionscheck/test_permissions_file_setuid_bit' in out


@pytest.mark.parametrize('package', ['binary/testsuidpermissionscheck'])
def test_permissions_missing_requires(tmp_path, package, permissions_check):
    output, test = permissions_check
    test.check(get_tested_package(package, tmp_path))
    out = output.print_results(output.results)
    assert "testsuidpermissionscheck.x86_64: E: permissions-missing-requires missing 'permissions' in PreReq" in out


@pytest.mark.parametrize('package', ['source/CheckInclude'])
def test_permissions_srcpackage(tmp_path, package, permissions_check):
    output, test = permissions_check
    test.check(get_tested_package(package, tmp_path))
    out = output.print_results(output.results)
    assert 'CheckInclude' not in out


@pytest.mark.parametrize('package', ['binary/sendmail'])
def test_permissions_d(tmp_path, package, permissions_check):
    output, test = permissions_check
    test.check(get_tested_package(package, tmp_path))
    out = output.print_results(output.results)
    assert 'sendmail.x86_64: E: permissions-file-setuid-bit /usr/sbin/sendmail is packaged with setuid/setgid bits (02555)' not in out


# https://github.com/rpm-software-management/rpmlint/issues/1292
PERMCTL_PKG = get_tested_mock_package(
    lazyload=True,
    name='permctl',
    files={
        '/var/lib/perms/test': {
            'is_dir': True,
            'metadata': {
                'mode': 0o640 | stat.S_IFDIR | stat.S_ISUID,
                'user': 'root',
                'group': 'root',
            },
        },
    },
    header={
        'POSTIN': """
  if [ -x /usr/bin/permctl ]; then \
    /usr/bin/permctl -n --set --system /var/lib/perms/test || : \
  fi \
""",
    },
)
CHKSTAT_PKG = PERMCTL_PKG.clone(
    header={
        'POSTIN': """
  if [ -x /usr/bin/chkstat ]; then \
    /usr/bin/chkstat -n --set --system /var/lib/perms/test || : \
  fi \
""",
    },
)


@pytest.mark.parametrize('package', [PERMCTL_PKG, CHKSTAT_PKG])
def test_permissions_permctl(package, permissions_check):
    output, test = permissions_check
    test.check(package)
    out = output.print_results(output.results)
    assert 'permissions-missing-postin' not in out
