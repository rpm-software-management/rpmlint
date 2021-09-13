import os

import pytest
from rpmlint.checks.SUIDPermissionsCheck import SUIDPermissionsCheck
from rpmlint.filter import Filter

import Testing
from Testing import get_tested_package


def get_suid_permissions_check(config_path):
    from rpmlint.config import Config

    if not os.path.isabs(config_path):
        config_path = Testing.testpath() / 'configs' / config_path
    config = Config([config_path])
    config.info = True
    output = Filter(config)
    test = SUIDPermissionsCheck(config, output)
    return output, test


@pytest.fixture(scope='function', autouse=True)
def permissions_check_profile(permissions_check):
    output, test = permissions_check
    test._parse_profile(str(Testing.testpath() / 'configs' / 'permissions.secure'))
    return output, test


@pytest.fixture(scope='function', autouse=True)
def permissions_check():
    return get_suid_permissions_check(Testing.TEST_CONFIG[0])


@pytest.mark.parametrize('package', ['binary/testsuidpermissionscheck'])
def test_permissions_symlink(tmpdir, package, permissions_check_profile):
    output, test = permissions_check_profile
    test.check(get_tested_package(package, tmpdir))
    out = output.print_results(output.results)
    assert 'testsuidpermissionscheck.x86_64: W: permissions-symlink /var/lib/testsuidpermissionscheck/test_permissions_symlink' in out


@pytest.mark.parametrize('package', ['binary/testsuidpermissionscheck'])
def test_permissions_dir_without_slash(tmpdir, package, permissions_check_profile):
    output, test = permissions_check_profile
    test.check(get_tested_package(package, tmpdir))
    out = output.print_results(output.results)
    assert 'testsuidpermissionscheck.x86_64: W: permissions-dir-without-slash /var/lib/testsuidpermissionscheck/test_permissions_dir_without_slash' in out


@pytest.mark.parametrize('package', ['binary/testsuidpermissionscheck'])
def test_permissions_incorrect(tmpdir, package, permissions_check_profile):
    output, test = permissions_check_profile
    test.check(get_tested_package(package, tmpdir))
    out = output.print_results(output.results)
    assert 'testsuidpermissionscheck.x86_64: E: permissions-incorrect /var/lib/testsuidpermissionscheck/test_permissions_incorrect has mode 0755 but should be 0600' in out


@pytest.mark.parametrize('package', ['binary/testsuidpermissionscheck'])
def test_permissions_incorrect_owner(tmpdir, package, permissions_check_profile):
    output, test = permissions_check_profile
    test.check(get_tested_package(package, tmpdir))
    out = output.print_results(output.results)
    assert 'testsuidpermissionscheck.x86_64: E: permissions-incorrect-owner /var/lib/testsuidpermissionscheck/test_permissions_incorrect_owner belongs to root:root but should be abc:root' in out


@pytest.mark.parametrize('package', ['binary/testsuidpermissionscheck'])
def test_permissions_fscaps(tmpdir, package, permissions_check):
    output, test = permissions_check
    test.check(get_tested_package(package, tmpdir))
    out = output.print_results(output.results)
    assert "testsuidpermissionscheck.x86_64: E: permissions-fscaps /var/lib/testsuidpermissionscheck/test_permissions_fscaps has fscaps 'cap_net_raw=ep'" in out


@pytest.mark.parametrize('package', ['binary/testsuidpermissionscheck'])
def test_permissions_file_setuid_bit(tmpdir, package, permissions_check):
    output, test = permissions_check
    test.check(get_tested_package(package, tmpdir))
    out = output.print_results(output.results)
    assert 'testsuidpermissionscheck.x86_64: E: permissions-file-setuid-bit /var/lib/testsuidpermissionscheck/test_non_position_independent_executable_and_suid is packaged with setuid/setgid bits (04755)' in out
    assert 'testsuidpermissionscheck.x86_64: E: permissions-file-setuid-bit /var/lib/testsuidpermissionscheck/test_permissions_file_setuid_bit is packaged with setuid/setgid bits (04755)' in out


@pytest.mark.parametrize('package', ['binary/testsuidpermissionscheck'])
def test_permissions_directory_setuid_bit(tmpdir, package, permissions_check):
    output, test = permissions_check
    test.check(get_tested_package(package, tmpdir))
    out = output.print_results(output.results)
    assert 'testsuidpermissionscheck.x86_64: E: permissions-directory-setuid-bit /var/lib/testsuidpermissionscheck/test_permissions_directory_setuid_bit is packaged with setuid/setgid bits (04755)' in out


@pytest.mark.parametrize('package', ['binary/permissions-no-postin'])
def test_permissions_missing_postin(tmpdir, package, permissions_check):
    output, test = permissions_check
    test.check(get_tested_package(package, tmpdir))
    out = output.print_results(output.results)
    assert 'permissions-no-postin.x86_64: E: permissions-missing-postin missing %set_permissions /var/lib/permissions-no-postin/test_permissions_directory_setuid_bit in %post' in out
    assert 'permissions-no-postin.x86_64: E: permissions-missing-postin missing %set_permissions /var/lib/permissions-no-postin/test_permissions_file_setuid_bit in %post' in out
    assert 'permissions-no-postin.x86_64: E: permissions-directory-setuid-bit /var/lib/permissions-no-postin/test_permissions_directory_setuid_bit is packaged with setuid/setgid bits (04755)' in out
    assert 'permissions-no-postin.x86_64: E: permissions-file-setuid-bit /var/lib/permissions-no-postin/test_permissions_file_setuid_bit is packaged with setuid/setgid bits (04755)' in out


@pytest.mark.parametrize('package', ['binary/testsuidpermissionscheck'])
def test_permissions_missing_verifyscript(tmpdir, package, permissions_check):
    output, test = permissions_check
    test.check(get_tested_package(package, tmpdir))
    out = output.print_results(output.results)
    assert 'testsuidpermissionscheck.x86_64: W: permissions-missing-verifyscript missing %verify_permissions -e /var/lib/testsuidpermissionscheck/test_non_position_independent_executable_and_suid' in out
    assert 'testsuidpermissionscheck.x86_64: W: permissions-missing-verifyscript missing %verify_permissions -e /var/lib/testsuidpermissionscheck/test_permissions_directory_setuid_bit' in out
    assert 'testsuidpermissionscheck.x86_64: W: permissions-missing-verifyscript missing %verify_permissions -e /var/lib/testsuidpermissionscheck/test_permissions_file_setuid_bit' in out


@pytest.mark.parametrize('package', ['binary/testsuidpermissionscheck'])
def test_permissions_missing_requires(tmpdir, package, permissions_check):
    output, test = permissions_check
    test.check(get_tested_package(package, tmpdir))
    out = output.print_results(output.results)
    assert "testsuidpermissionscheck.x86_64: E: permissions-missing-requires missing 'permissions' in PreReq" in out


@pytest.mark.parametrize('package', ['source/CheckInclude'])
def test_permissions_srcpackage(tmpdir, package, permissions_check):
    output, test = permissions_check
    test.check(get_tested_package(package, tmpdir))
    out = output.print_results(output.results)
    assert 'CheckInclude' not in out


@pytest.mark.parametrize('package', ['binary/sendmail'])
def test_permissions_d(tmpdir, package, permissions_check):
    output, test = permissions_check
    test.check(get_tested_package(package, tmpdir))
    out = output.print_results(output.results)
    assert 'sendmail.x86_64: E: permissions-file-setuid-bit /usr/sbin/sendmail is packaged with setuid/setgid bits (02555)' not in out
