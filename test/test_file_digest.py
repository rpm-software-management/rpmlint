import os

import pytest
from rpmlint.checks.FileDigestCheck import FileDigestCheck
from rpmlint.filter import Filter
from rpmlint.pkg import FakePkg

import Testing
from Testing import get_tested_package


def get_digestcheck(config_path):
    from rpmlint.config import Config
    if not os.path.isabs(config_path):
        config_path = Testing.testpath() / 'configs' / config_path
    config = Config([config_path])
    config.info = True
    output = Filter(config)
    test = FileDigestCheck(config, output)
    return output, test


@pytest.fixture(scope='function', autouse=True)
def digestcheck():
    return get_digestcheck(Testing.TEST_CONFIG[0])


@pytest.mark.parametrize('package', ['binary/file-signature-good'])
def test_signatures(tmpdir, package, digestcheck):
    output, test = digestcheck
    test.check(get_tested_package(package, tmpdir))
    out = output.print_results(output.results)
    assert not out


@pytest.mark.parametrize('package', ['binary/file-signature-symlinks'])
def test_signatures_symlinks(tmpdir, package, digestcheck):
    output, test = digestcheck
    test.check(get_tested_package(package, tmpdir))
    out = output.print_results(output.results)
    assert len(output.results) == 2
    assert 'file-signature-symlinks.x86_64: E: cron-file-symlink /etc/cron.daily/symlink' in out
    assert 'file-signature-symlinks.x86_64: E: cron-file-digest-ghost /etc/cron.daily/test-me-ghost' in out


@pytest.mark.parametrize('package', ['binary/file-signature-bad'])
def test_signatures_bad(tmpdir, package, digestcheck):
    output, test = digestcheck
    test.check(get_tested_package(package, tmpdir))
    out = output.print_results(output.results)
    assert len(output.results) == 1
    assert 'file-signature-bad.x86_64: E: cron-file-digest-mismatch /etc/cron.daily/suse.de-sarg expected sha256:edeaaff3f1774ad2888673770c6d64097e391bc362d7d6fb34982ddf0efd18cb, has:8dbb513cddb18fe825dad6836161e03c109de7736913444dd5ad3de9d5579afe' in out


def test_description_message(tmpdir, digestcheck):
    output, test = digestcheck
    assert 'https://en.opensuse.org/openSUSE:Package_security_guidelines#audit_bugs' in output.get_description('cron-file-digest-unauthorized')


def test_matching_digests():
    output, test = get_digestcheck('digests.config')
    with FakePkg('testpkg') as pkg:
        pkg.add_file_with_content('/restricted/1/dangerous', 'really dangerous stuff')
        # also test following of symlinks with this entry
        pkg.add_symlink_to('/alsorestricted/2/suspicious', '/other/place/suspicious.txt')
        pkg.add_file_with_content('/other/place/suspicious.txt', 'really suspicious stuff')
        pkg.add_file_with_content('/related/and/also/sensitive', 'related sensitive stuff')
        test.check(pkg)
        assert len(output.results) == 0


def test_simple_mismatch():
    output, test = get_digestcheck('digests.config')
    with FakePkg('testpkg') as pkg:
        pkg.add_file_with_content('/restricted/1/dangerous', 'really dangerous stuff')
        pkg.add_symlink_to('/alsorestricted/2/suspicious', '/other/place/suspicious.txt')
        pkg.add_file_with_content('/other/place/suspicious.txt', 'really good stuff')
        pkg.add_file_with_content('/related/and/also/sensitive', 'related sensitive stuff')
        test.check(pkg)
        assert len(output.results) == 1
        error = output.results[0]
        assert error.startswith('testpkg: E: somerestriction-file-digest-mismatch /alsorestricted/2/suspicious expected sha256:')


def test_related_mismatch():
    # this tests that a related file digest mismatch triggers correctly
    output, test = get_digestcheck('digests.config')
    with FakePkg('testpkg') as pkg:
        pkg.add_file_with_content('/restricted/1/dangerous', 'really dangerous stuff')
        pkg.add_symlink_to('/alsorestricted/2/suspicious', '/other/place/suspicious.txt')
        pkg.add_file_with_content('/other/place/suspicious.txt', 'really suspicious stuff')
        pkg.add_file_with_content('/related/and/also/sensitive', 'related fine stuff')
        test.check(pkg)
        assert len(output.results) == 1
        error = output.results[0]
        assert error.startswith('testpkg: E: somerestriction-file-digest-mismatch /related/and/also/sensitive expected sha1:')


def test_missing_entry():
    # this tests that an extra file not present in the whitelist is recognized
    # as missing
    output, test = get_digestcheck('digests.config')
    with FakePkg('testpkg') as pkg:
        pkg.add_file_with_content('/restricted/1/dangerous', 'really dangerous stuff')
        pkg.add_symlink_to('/alsorestricted/2/suspicious', '/other/place/suspicious.txt')
        pkg.add_file_with_content('/other/place/suspicious.txt', 'really suspicious stuff')
        pkg.add_file_with_content('/related/and/also/sensitive', 'related sensitive stuff')
        pkg.add_file_with_content('/restricted/1/evil', 'evil stuff')
        test.check(pkg)
        assert len(output.results) == 1
        error = output.results[0]
        assert error == 'testpkg: E: somerestriction-file-digest-unauthorized /restricted/1/evil (file digest sha256:f2175fc16d5a482baa71b2e77831b354afa91a5fda5ef0df59d8e87376598d4f)'


@pytest.mark.parametrize('package', ['binary/tmpwatch'])
def test_file_digest_mismatch(tmpdir, package):
    output, test = get_digestcheck('digests2.config')
    test.check(get_tested_package(package, tmpdir))
    out = output.print_results(output.results)
    assert 'tmpwatch.x86_64: E: cron-file-digest-unauthorized /etc/cron.daily/tmpwatch' not in out
    assert 'tmpwatch.x86_64: E: cron-file-digest-mismatch /etc/cron.daily/tmpwatch' in out


def test_wrong_pkg_name():
    # this tests that a package with matching entries but mismatching package
    # name does not pass the check
    output, test = get_digestcheck('digests.config')
    with FakePkg('otherpkg') as pkg:
        pkg.add_file_with_content('/restricted/1/dangerous', 'really dangerous stuff')
        # also test following of symlinks with this entry
        pkg.add_symlink_to('/alsorestricted/2/suspicious', '/other/place/suspicious.txt')
        pkg.add_file_with_content('/other/place/suspicious.txt', 'really suspicious stuff')
        pkg.add_file_with_content('/related/and/also/sensitive', 'related sensitive stuff')
        test.check(pkg)
        assert len(output.results) == 2
        assert 'otherpkg: E: somerestriction-file-digest-unauthorized /alsorestricted/2/suspicious (file digest of resolved path /other/place/suspicious.txt sha256:a412bca55af87ea264063df10d08a40ff3b8e68106f4a48a3c4a1cacb6394c94)' in output.results
        assert 'otherpkg: E: somerestriction-file-digest-unauthorized /restricted/1/dangerous (file digest sha256:537b320f9c3b30276bd54b838b6e6b72e923e70dbdb126926f992d594a30256c)' in output.results


def test_unaffected_pkg():
    # this tests that a package that doesn't contain any files in restricted
    # locations doesn't trigger any errors.
    output, test = get_digestcheck('digests.config')
    with FakePkg('cleanpkg') as pkg:
        pkg.add_file_with_content('/arbitrary/file', 'arbitrary content')
        test.check(pkg)
        assert len(output.results) == 0


def test_matching_nodigests():
    output, test = get_digestcheck('nodigests.config')
    with FakePkg('testpkg') as pkg:
        pkg.add_file_with_content('/restricted/1/dangerous', 'whatever')
        # also test following of symlinks with this entry
        pkg.add_symlink_to('/alsorestricted/2/suspicious', '/other/place/suspicious.txt')
        pkg.add_file_with_content('/other/place/suspicious.txt', 'whatever')
        pkg.add_file_with_content('/related/and/also/sensitive', 'related sensitive stuff')
        test.check(pkg)
        assert len(output.results) == 0


def test_missing_nodigests_entry():
    # this tests that an extra file not present in the nodigest whitelist is recognized
    # as missing
    output, test = get_digestcheck('nodigests.config')
    with FakePkg('testpkg') as pkg:
        pkg.add_file_with_content('/restricted/1/dangerous', 'whatever')
        pkg.add_symlink_to('/alsorestricted/2/suspicious', '/other/place/suspicious.txt')
        pkg.add_file_with_content('/other/place/suspicious.txt', 'whatever')
        pkg.add_file_with_content('/related/and/also/sensitive', 'related sensitive stuff')
        pkg.add_file_with_content('/restricted/1/evil', 'evil stuff')
        test.check(pkg)
        assert len(output.results) == 1
        error = output.results[0]
        assert error == 'testpkg: E: somerestriction-file-digest-unauthorized /restricted/1/evil (file digest sha256:f2175fc16d5a482baa71b2e77831b354afa91a5fda5ef0df59d8e87376598d4f)'


def test_wrong_pkg_name_for_nodigests():
    # this tests that a package with matching entries but mismatching package
    # name does not pass the check
    output, test = get_digestcheck('nodigests.config')
    with FakePkg('otherpkg') as pkg:
        pkg.add_file_with_content('/restricted/1/dangerous', 'whatever')
        # also test following of symlinks with this entry
        pkg.add_symlink_to('/alsorestricted/2/suspicious', '/other/place/suspicious.txt')
        pkg.add_file_with_content('/other/place/suspicious.txt', 'whatever')
        pkg.add_file_with_content('/related/and/also/sensitive', 'whatever')
        test.check(pkg)
        assert len(output.results) == 2
        assert 'otherpkg: E: somerestriction-file-digest-unauthorized /alsorestricted/2/suspicious (file digest of resolved path /other/place/suspicious.txt sha256:85738f8f9a7f1b04b5329c590ebcb9e425925c6d0984089c43a022de4f19c281)' in output.results
        assert 'otherpkg: E: somerestriction-file-digest-unauthorized /restricted/1/dangerous (file digest sha256:85738f8f9a7f1b04b5329c590ebcb9e425925c6d0984089c43a022de4f19c281)' in output.results


def test_combination_nodigests_and_digests():
    # this tests that an extra file not present in the nodigest whitelist is recognized
    # as missing
    output, test = get_digestcheck('nodigests.config')
    with FakePkg('testpkg') as pkg:
        pkg.add_file_with_content('/restricted/1/dangerous', 'whatever')
        pkg.add_symlink_to('/alsorestricted/2/suspicious', '/other/place/suspicious.txt')
        pkg.add_file_with_content('/other/place/suspicious.txt', 'whatever')
        pkg.add_file_with_content('/related/and/also/sensitive', 'wrong content')
        test.check(pkg)
        assert len(output.results) == 1
        error = output.results[0]
        assert error == 'testpkg: E: somerestriction-file-digest-mismatch /related/and/also/sensitive expected sha1:ab5ec199027247773d2d617895f49179d7b3186e, has:a6abec9ea1e13ca93d1c704758bd52f62ef16433'


@pytest.mark.parametrize('package', ['binary/pam-module'])
def test_pam_modules(tmpdir, package, digestcheck):
    output, test = get_digestcheck('digests_pam.config')
    test.check(get_tested_package(package, tmpdir))
    out = output.print_results(output.results)
    assert 'pam-module.x86_64: E: pamempty-file-digest-unauthorized /usr/lib64/security/pam-module.so' in out


@pytest.mark.parametrize('package', ['binary/pam-module'])
def test_pam_includeonly_nonexistent(tmpdir, package, digestcheck):
    output, test = get_digestcheck('digests_pam1.config')
    test.check(get_tested_package(package, tmpdir))
    out = output.print_results(output.results)
    assert 'pamincludetxt' not in out


@pytest.mark.parametrize('package', ['binary/pam-module'])
def test_pam_includeonly_existent(tmpdir, package, digestcheck):
    output, test = get_digestcheck('digests_pam2.config')
    test.check(get_tested_package(package, tmpdir))
    out = output.print_results(output.results)
    assert 'pam-module.x86_64: E: pamincludeso-file-digest-unauthorized /usr/lib64/security/pam-module.so' in out


@pytest.mark.parametrize('package', ['binary/pam-module'])
def test_pam(tmpdir, package, digestcheck):
    output, test = get_digestcheck('digests_pam3.config')
    test.check(get_tested_package(package, tmpdir))
    out = output.print_results(output.results)
    assert not out
