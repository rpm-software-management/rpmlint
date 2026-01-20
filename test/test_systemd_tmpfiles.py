import os

import pytest
from rpmlint.checks.SystemdTmpfilesCheck import SystemdTmpfilesCheck
from rpmlint.config import Config
from rpmlint.filter import Filter
from rpmlint.pkg import FakePkg

import Testing
from Testing import get_tested_path


def get_tmpfilescheck(config_path):
    if not os.path.isabs(config_path):
        config_path = get_tested_path('configs', config_path)
    config = Config([config_path])
    config.info = True
    output = Filter(config)
    test = SystemdTmpfilesCheck(config, output)
    return output, test, config


@pytest.fixture(scope='function', autouse=True)
def tmpfilescheck():
    return get_tmpfilescheck(Testing.TEST_CONFIG[0])


def test_dropin_dir_restriction(tmpfilescheck):
    # basic test that restricted systemd-tmpfiles items are complained about
    output, test, config = tmpfilescheck
    with FakePkg('testpkg') as pkg:
        for dropindir in config.configuration['SystemdTmpfiles'].get('DropinDirs'):
            pkg.add_file_with_content(f'{dropindir}/some.conf', 'd /run/somedir 1777 root root')
            # make sure parse errors are handled correctly
            pkg.add_file_with_content(f'{dropindir}/broken.conf', 'broken')
            # also test rejection of symlinks
            pkg.add_symlink_to(f'{dropindir}/link.conf', '/some/where/some.conf')
            # ... and ghost files
            pkg.add_ghost(f'{dropindir}/ghost.conf')
            # make sure non-sensitive entries *don't* trigger a report
            pkg.add_file_with_content(f'{dropindir}/harmless.conf', 'd /run/harmless 750 root root')
            # make sure files not ending in *.conf are ignored
            pkg.add_file_with_content(f'{dropindir}/harmless', 'd /run/somedir 1777 root root')

        # now the same in a non-restricted directory
        pkg.add_file_with_content('/harmless/some.conf', 'd /run/somedir 1777 root root')
        pkg.add_symlink_to('/harmless/link.conf', '/some/where/some.conf')
        pkg.add_ghost('/harmless/ghost.conf')

        test.check(pkg)

        # make sure the non-restricted items have not been complained about
        assert 'harmless' not in ''.join(output.results)

        for expected in (
                'testpkg: E: systemd-tmpfile-entry-unauthorized /tmpfiles1/some.conf "d /run/somedir 1777 root root"',
                'testpkg: E: systemd-tmpfile-ghost /tmpfiles2/ghost.conf',
                'testpkg: E: systemd-tmpfile-symlink /tmpfiles2/link.conf',
                'testpkg: E: systemd-tmpfile-parse-error /tmpfiles2/broken.conf broken /tmpfiles2/broken.conf:broken: Too few fields encountered'):
            assert expected in output.results


def test_whitelistings(tmpfilescheck):
    # this tests whether a valid whitelisting is correctly accepted for
    # sensitive entries.
    # furthermore pkg name restrictions are checked
    output, test, config = tmpfilescheck
    for pkgname in ('goodpkg', 'badpkg'):
        with FakePkg(pkgname) as pkg:
            pkg.add_file_with_content('/tmpfiles1/some.conf', 'd /tmp/.rpmlint-stuff 0777 root root -')
            pkg.add_file_with_content('/tmpfiles2/other.conf', 'd /tmp/.more-stuff 0777 root root -')
            test.check(pkg)
            if pkgname == 'goodpkg':
                assert 'systemd-tmpfile-entry-unauthorized' not in ''.join(output.results)
            else:
                assert 'systemd-tmpfile-entry-unauthorized' in ''.join(output.results)


def test_parser(tmpfilescheck):
    # this simply tests whether various tmpfiles.d configuration parser code
    # paths are robust
    output, test, config = tmpfilescheck

    LINES = (
        'L /some/path 0777 root root - -',
        'R /some/path - - - - -',
        'X /some/path - - - - -',
        'd /some/path 0755 root root 1d -',
        'd /some/path - root root 1d -',
        'f /some/path 4755 root root - -',
        'c /some/path 0755 someone root - -',
        'h /some/path - - - - +C',
        'h /some/path - - - - +a',
        "f '/quoted/field with spaces' 0777 root root - -",
        'f "/quoted/field with spaces" 0777 root root - -',
        'f /some/path 0777 root root -   trailing spaces  ',
    )

    with FakePkg('testpkg') as pkg:
        pkg.add_file_with_content('/tmpfiles1/complex.conf', '\n'.join(LINES))
        test.check(pkg)
