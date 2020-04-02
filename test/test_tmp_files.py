import pytest
from rpmlint.checks.TmpFilesCheck import TmpFilesCheck
from rpmlint.filter import Filter

from Testing import CONFIG, get_tested_package


@pytest.fixture(scope='function', autouse=True)
def tmpfilescheck():
    CONFIG.info = True
    output = Filter(CONFIG)
    test = TmpFilesCheck(CONFIG, output)
    return output, test


@pytest.mark.parametrize('package', ['binary/tempfiled'])
def test_tmpfiles(tmpdir, package, tmpfilescheck):
    output, test = tmpfilescheck
    test.check(get_tested_package(package, tmpdir))
    out = output.print_results(output.results)

    assert 'W: pre-with-tmpfile-creation ' not in out
    assert 'W: post-without-tmpfile-creation /usr/lib/tmpfiles.d/krb5.conf' in out
    assert 'W: tmpfile-not-in-filelist /var/lib/kerberos' in out
    assert 'W: tmpfile-not-regular-file /usr/lib/tmpfiles.d/symlink.conf' in out


@pytest.mark.parametrize('package', ['binary/systemd-tmpfiles'])
def test_tmpfiles2(tmpdir, package, tmpfilescheck):
    output, test = tmpfilescheck
    test.check(get_tested_package(package, tmpdir))
    out = output.print_results(output.results)

    assert 'W: pre-with-tmpfile-creation /usr/lib/tmpfiles.d/systemd-tmpfiles.conf' in out
    assert 'W: post-without-tmpfile-creation' in out
    assert 'W: tmpfile-not-in-filelist /run/my_new_directory' in out
    assert 'W: tmpfile-not-regular-file' not in out


@pytest.mark.parametrize('package', ['binary/systemd-tmpfiles_correct'])
def test_tmpfiles_correct(tmpdir, package, tmpfilescheck):
    output, test = tmpfilescheck
    test.check(get_tested_package(package, tmpdir))
    out = output.print_results(output.results)

    assert 'W: pre-with-tmpfile-creation' not in out
    assert 'W: post-without-tmpfile-creation' not in out
    assert 'W: tmpfile-not-regular-file' not in out
    assert 'W: tmpfile-not-in-filelist' not in out
