import os

import pytest
from rpmlint.checks.FileDigestCheck import FileDigestCheck
from rpmlint.filter import Filter
from rpmlint.pkg import FakePkg

import Testing
from Testing import get_tested_package, get_tested_path


def get_digestcheck(config_path):
    from rpmlint.config import Config
    if not os.path.isabs(config_path):
        config_path = get_tested_path('configs', config_path)
    config = Config([config_path])
    config.info = True
    output = Filter(config)
    test = FileDigestCheck(config, output)
    return output, test


@pytest.fixture(scope='function', autouse=True)
def digestcheck():
    return get_digestcheck(Testing.TEST_CONFIG[0])


@pytest.mark.parametrize('package', ['binary/file-signature-good'])
def test_signatures(tmp_path, package, digestcheck):
    output, test = digestcheck
    test.check(get_tested_package(package, tmp_path))
    out = output.print_results(output.results)
    assert not out


@pytest.mark.parametrize('package', ['binary/file-signature-symlinks'])
def test_signatures_symlinks(tmp_path, package, digestcheck):
    output, test = digestcheck
    test.check(get_tested_package(package, tmp_path))
    out = output.print_results(output.results)
    assert len(output.results) == 2
    assert 'file-signature-symlinks.x86_64: E: cron-file-symlink /etc/cron.daily/symlink' in out
    assert 'file-signature-symlinks.x86_64: E: cron-file-ghost /etc/cron.daily/test-me-ghost' in out


@pytest.mark.parametrize('package', ['binary/file-signature-bad'])
def test_signatures_bad(tmp_path, package, digestcheck):
    output, test = digestcheck
    test.check(get_tested_package(package, tmp_path))
    out = output.print_results(output.results)
    assert len(output.results) == 1
    assert 'file-signature-bad.x86_64: E: cron-file-digest-mismatch /etc/cron.daily/suse.de-sarg expected sha256:edeaaff3f1774ad2888673770c6d64097e391bc362d7d6fb34982ddf0efd18cb, has:8dbb513cddb18fe825dad6836161e03c109de7736913444dd5ad3de9d5579afe' in out


def test_description_message(tmp_path, digestcheck):
    output, test = digestcheck
    assert 'https://en.opensuse.org/openSUSE:Package_security_guidelines#audit_bugs' in output.get_description('cron-file-unauthorized')


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
        assert error == 'testpkg: E: somerestriction-file-unauthorized /restricted/1/evil (sha256 file digest default filter:f2175fc16d5a482baa71b2e77831b354afa91a5fda5ef0df59d8e87376598d4f shell filter:8336ce7a3fb22e404a767f7b7302cfc6637083fa1b4fd63fe11c2d977d65dfa2 xml filter:<failed-to-calculate>)'


@pytest.mark.parametrize('package', ['binary/tmpwatch'])
def test_file_digest_mismatch(tmp_path, package):
    output, test = get_digestcheck('digests2.config')
    test.check(get_tested_package(package, tmp_path))
    out = output.print_results(output.results)
    assert 'tmpwatch.x86_64: E: cron-file-unauthorized /etc/cron.daily/tmpwatch' not in out
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
        assert 'otherpkg: E: somerestriction-file-unauthorized /alsorestricted/2/suspicious (sha256 file digest of resolved path /other/place/suspicious.txt default filter:a412bca55af87ea264063df10d08a40ff3b8e68106f4a48a3c4a1cacb6394c94 shell filter:26f40cba5d4f8d6ff9815a12890fb1dbc9e32771a29ccc4ecbb300475dfeb057 xml filter:<failed-to-calculate>)' in output.results
        assert 'otherpkg: E: somerestriction-file-unauthorized /restricted/1/dangerous (sha256 file digest default filter:537b320f9c3b30276bd54b838b6e6b72e923e70dbdb126926f992d594a30256c shell filter:eb372739a52b2c1a400038e1bea1ff3e194ed2a2986d098d01fd631fb3f29c81 xml filter:<failed-to-calculate>)' in output.results


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
        assert error == 'testpkg: E: somerestriction-file-unauthorized /restricted/1/evil (sha256 file digest default filter:f2175fc16d5a482baa71b2e77831b354afa91a5fda5ef0df59d8e87376598d4f shell filter:8336ce7a3fb22e404a767f7b7302cfc6637083fa1b4fd63fe11c2d977d65dfa2 xml filter:<failed-to-calculate>)'


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
        assert 'otherpkg: E: somerestriction-file-unauthorized /alsorestricted/2/suspicious (sha256 file digest of resolved path /other/place/suspicious.txt default filter:85738f8f9a7f1b04b5329c590ebcb9e425925c6d0984089c43a022de4f19c281 shell filter:cd293be6cea034bd45a0352775a219ef5dc7825ce55d1f7dae9762d80ce64411 xml filter:<failed-to-calculate>)' in output.results
        assert 'otherpkg: E: somerestriction-file-unauthorized /restricted/1/dangerous (sha256 file digest default filter:85738f8f9a7f1b04b5329c590ebcb9e425925c6d0984089c43a022de4f19c281 shell filter:cd293be6cea034bd45a0352775a219ef5dc7825ce55d1f7dae9762d80ce64411 xml filter:<failed-to-calculate>)' in output.results


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


def test_multiple_packages():
    # the first two should match, the last one shouldn't
    for pkgname in ('testpkg2', 'otherpkg', 'badpkg'):
        with FakePkg(pkgname) as pkg:
            pkg.add_file_with_content('/restricted/1/afile', 'some file content')
            output, test = get_digestcheck('digests.config')
            test.check(pkg)

            if pkgname != 'badpkg':
                assert len(output.results) == 0
            else:
                error = output.results[0]
                assert error.startswith(f'{pkgname}: E: somerestriction-file-unauthorized /restricted/1/afile')


def test_shell_digest_filter():
    with open(get_tested_path('data/shell_digest.sh')) as f:
        shell_script = f.read()

    output, test = get_digestcheck('digests_filtered.config')
    with FakePkg('shellpkg') as pkg:
        pkg.add_file_with_content('/shell/test.sh', shell_script)
        test.check(pkg)
        assert len(output.results) == 0

    # the same file with removed empty lines and whitespace should result in
    # the same digest
    output, test = get_digestcheck('digests_filtered.config')
    with FakePkg('shellpkg') as pkg:
        trimmed_script = '\n'.join([line.rstrip() for line in shell_script.splitlines() if line])
        pkg.add_file_with_content('/shell/test.sh', trimmed_script)
        test.check(pkg)
        assert len(output.results) == 0

    # the file with changed actual code should result in a digest mismatch
    output, test = get_digestcheck('digests_filtered.config')
    with FakePkg('shellpkg') as pkg:
        changed_script = shell_script.replace('seq 10', 'seq 11')
        pkg.add_file_with_content('/shell/test.sh', changed_script)
        test.check(pkg)
        assert len(output.results) == 1


def test_xml_digest_filter():
    with open(get_tested_path('data/xml_digest.xml')) as f:
        xml_data = f.read()

    output, test = get_digestcheck('digests_filtered.config')
    with FakePkg('xmlpkg') as pkg:
        pkg.add_file_with_content('/xml/test.xml', xml_data)
        test.check(pkg)
        assert len(output.results) == 0

    # the stripped XML should still result in the same digest
    output, test = get_digestcheck('digests_filtered.config')
    with FakePkg('xmlpkg') as pkg:
        stripped_xml = '\n'.join([line.strip() for line in xml_data.splitlines() if line])
        pkg.add_file_with_content('/xml/test.xml', stripped_xml)
        test.check(pkg)
        assert len(output.results) == 0

    # actually changed content should result in a whitelisting error
    output, test = get_digestcheck('digests_filtered.config')
    with FakePkg('xmlpkg') as pkg:
        changed_xml = xml_data.replace('"root"', '"nobody"')
        pkg.add_file_with_content('/xml/test.xml', changed_xml)
        test.check(pkg)
        assert len(output.results) == 1


def test_default_digester():
    SOME_DATA = '   hello there   '
    output, test = get_digestcheck('digests_filtered.config')
    with FakePkg('defaultpkg') as pkg:
        pkg.add_file_with_content('/default/some.txt', SOME_DATA)
        test.check(pkg)
        assert len(output.results) == 0

    # changing whitespace should also change the digest
    output, test = get_digestcheck('digests_filtered.config')
    with FakePkg('defaultpkg') as pkg:
        pkg.add_file_with_content('/default/some.txt', SOME_DATA.strip())
        test.check(pkg)
        assert len(output.results) == 1


@pytest.mark.parametrize('package', ['binary/pam-module'])
def test_pam_modules(tmp_path, package, digestcheck):
    output, test = get_digestcheck('digests_pam.config')
    test.check(get_tested_package(package, tmp_path))
    out = output.print_results(output.results)
    assert 'pam-module.x86_64: E: pamempty-file-unauthorized /usr/lib64/security/pam-module.so' in out


@pytest.mark.parametrize('package', ['binary/pam-module'])
def test_pam_includeonly_nonexistent(tmp_path, package, digestcheck):
    output, test = get_digestcheck('digests_pam1.config')
    test.check(get_tested_package(package, tmp_path))
    out = output.print_results(output.results)
    assert 'pamincludetxt' not in out


@pytest.mark.parametrize('package', ['binary/pam-module'])
def test_pam_includeonly_existent(tmp_path, package, digestcheck):
    output, test = get_digestcheck('digests_pam2.config')
    test.check(get_tested_package(package, tmp_path))
    out = output.print_results(output.results)
    assert 'pam-module.x86_64: E: pamincludeso-file-unauthorized /usr/lib64/security/pam-module.so' in out


@pytest.mark.parametrize('package', ['binary/pam-module'])
def test_pam(tmp_path, package, digestcheck):
    output, test = get_digestcheck('digests_pam3.config')
    test.check(get_tested_package(package, tmp_path))
    out = output.print_results(output.results)
    assert not out
