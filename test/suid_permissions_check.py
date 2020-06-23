import os
import stat

import pytest
import rpm
from rpmlint.checks.SUIDPermissionsCheck import SUIDCheck
from rpmlint.filter import Filter
from rpmlint.pkg import FakePkg, PkgFile

from Testing import CONFIG, get_tested_package


@pytest.fixture(scope='function', autouse=True)
def suid_check(tmpdir):
    CONFIG.info = True
    output = Filter(CONFIG)
    test = SUIDCheck(CONFIG, output)

    # set the allow list of expected/allowed permissions, matching suid-test-0-0.x86_64.rpm
    test.perms = {
        '/bin/suid_root': {'owner': 'root:root', 'mode': 0o4750},
        '/suid_root_dir/': {'owner': 'root:root', 'mode': 0o2750},
    }

    return output, test


@pytest.mark.parametrize('package', ['binary/suid-with-scripts'])
def test_suid_ok(tmpdir, package, suid_check):
    output, test = suid_check
    test.check(get_tested_package(package, tmpdir))
    out = output.print_results(output.results)
    assert out == ''


@pytest.mark.parametrize('package', ['binary/suid-with-scripts'])
def test_suid_dir_without_slash(tmpdir, package, suid_check):
    output, test = suid_check
    test.perms['/suid_root_dir'] = test.perms['/suid_root_dir/']
    del test.perms['/suid_root_dir/']

    test.check(get_tested_package(package, tmpdir))
    out = output.print_results(output.results)
    assert 'noproblem' not in out
    assert 'permissions-dir-without-slash /suid_root_dir' in out


@pytest.mark.parametrize('package', ['binary/suid-with-scripts'])
def test_suid_file_as_dir(tmpdir, package, suid_check):
    output, test = suid_check
    test.perms['/bin/suid_root/'] = test.perms['/bin/suid_root']
    del test.perms['/bin/suid_root']

    test.check(get_tested_package(package, tmpdir))
    out = output.print_results(output.results)
    assert 'noproblem' not in out
    assert 'permissions-file-as-dir /bin/suid_root' in out
    assert 'non-position-independent-executable /bin/suid_root' in out
    assert 'permissions-file-setuid-bit /bin/suid_root' in out


@pytest.mark.parametrize('package', ['binary/suid-no-scripts'])
def test_suid_missing_scripts(tmpdir, package, suid_check):
    output, test = suid_check
    test.check(get_tested_package(package, tmpdir))
    out = output.print_results(output.results)
    assert 'noproblem' not in out
    assert 'permissions-missing-requires' in out
    assert 'permissions-missing-verifyscript' in out
    assert 'permissions-missing-postin' in out


@pytest.mark.parametrize('package', ['binary/suid-with-scripts'])
def test_suid_non_allowed(tmpdir, package, suid_check):
    output, test = suid_check
    test.perms = {}

    test.check(get_tested_package(package, tmpdir))
    out = output.print_results(output.results)
    assert 'noproblem' not in out
    assert 'permissions-directory-setuid-bit' in out
    assert 'permissions-file-setuid-bit' in out


def test_suid_unauthorized_permissions(suid_check):
    output, test = suid_check

    unauth_file = PkgFile('/usr/share/permissions/permissions.d/unauthorized')
    unauth_file.user = 'root'
    unauth_file.group = 'root'
    unauth_file.filecaps = '+caps'
    ghost_file = PkgFile('/etc/permissions.d/ghost')
    ghost_file.user = 'root'
    ghost_file.group = 'root'
    ghost_file.flags = rpm.RPMFILE_GHOST

    with FakePkg('suid', [unauth_file, ghost_file]) as package:
        package.is_source = False

        os.makedirs(os.path.dirname(package.dirName() + '/' + unauth_file.name))
        open(package.dirName() + '/' + unauth_file.name, 'w').close()

        test.check(package)

    out = output.print_results(output.results)
    assert 'noproblem' not in out
    assert 'permissions-unauthorized-file /usr/share/permissions/permissions.d/unauthorized' in out
    assert 'permissions-fscaps /usr/share/permissions/permissions.d/unauthorized' in out
    assert 'permissions-ghostfile /etc/permissions.d/ghost' in out


@pytest.mark.parametrize('package', ['binary/suid-with-scripts'])
def test_suid_world_writable(tmpdir, package, suid_check):
    output, test = suid_check

    pkg = get_tested_package(package, tmpdir)
    pkg.files['/bin/suid_root'].mode |= stat.S_IWOTH
    del test.perms['/bin/suid_root']
    test.check(pkg)

    out = output.print_results(output.results)
    assert 'noproblem' not in out
    assert 'permissions-world-writable /bin/suid_root' in out


@pytest.mark.parametrize('package', ['binary/suid-with-scripts'])
def test_suid_incorrect(tmpdir, package, suid_check):
    output, test = suid_check

    test.perms['/bin/suid_root']['owner'] = 'foo:bar'
    test.perms['/bin/suid_root']['mode'] = 0
    test.check(get_tested_package(package, tmpdir))

    out = output.print_results(output.results)
    assert 'noproblem' not in out
    assert 'permissions-incorrect-owner /bin/suid_root' in out
    assert 'permissions-incorrect /bin/suid_root' in out


@pytest.mark.parametrize('package', ['binary/suid-with-scripts'])
def test_suid_symlink(tmpdir, package, suid_check):
    output, test = suid_check

    pkg = get_tested_package(package, tmpdir)
    pkg.files['/bin/suid_root'].mode = (pkg.files['/bin/suid_root'].mode ^ stat.S_IFREG) | stat.S_IFLNK
    test.check(pkg)

    out = output.print_results(output.results)
    assert 'noproblem' not in out
    assert 'permissions-symlink /bin/suid_root' in out
