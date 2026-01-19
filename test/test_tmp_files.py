from mockdata.mock_tmp_files import (
    SystemdTempfilesOkPackage,
    SystemdTempfilesPackage,
    TempfiledPackage,
)
import pytest
from rpmlint.checks.TmpFilesCheck import TmpFilesCheck
from rpmlint.filter import Filter

from Testing import CONFIG


@pytest.fixture(scope='function', autouse=True)
def tmpfilescheck():
    CONFIG.info = True
    output = Filter(CONFIG)
    test = TmpFilesCheck(CONFIG, output)
    return output, test


@pytest.mark.parametrize('package', [TempfiledPackage])
def test_tmpfiles(package, tmpfilescheck):
    output, test = tmpfilescheck
    test.check(package)
    out = output.print_results(output.results)

    assert 'W: pre-with-tmpfile-creation ' not in out
    assert 'W: tmpfile-not-in-filelist /var/lib/kerberos' in out
    assert 'W: tmpfile-not-regular-file /usr/lib/tmpfiles.d/symlink.conf' in out


@pytest.mark.parametrize('package', [SystemdTempfilesPackage])
def test_tmpfiles2(package, tmpfilescheck):
    output, test = tmpfilescheck
    test.check(package)
    out = output.print_results(output.results)

    assert 'W: pre-with-tmpfile-creation /usr/lib/tmpfiles.d/systemd-tmpfiles.conf' in out
    assert 'W: tmpfile-not-in-filelist /run/my_new_directory' in out
    assert 'W: tmpfile-not-regular-file' not in out


@pytest.mark.parametrize('package', [SystemdTempfilesOkPackage])
def test_tmpfiles_correct(package, tmpfilescheck):
    output, test = tmpfilescheck
    test.check(package)
    out = output.print_results(output.results)

    assert 'W: pre-with-tmpfile-creation' not in out
    assert 'W: tmpfile-not-regular-file' not in out
    assert 'W: tmpfile-not-in-filelist' not in out
