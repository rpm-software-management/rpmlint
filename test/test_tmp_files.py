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
def test_bashisms(tmpdir, package, tmpfilescheck):
    output, test = tmpfilescheck
    test.check(get_tested_package(package, tmpdir))
    out = output.print_results(output.results)

    assert 'W: postin-without-tmpfile-creation /usr/lib/tmpfiles.d/krb5.conf' in out
    assert 'W: postin-without-ghost-file-creation /tmp/foo' in out
    assert 'W: tmpfile-not-ghost /var/lib/kerberos' in out
    assert 'W: ghost-files-without-postin' in out
    assert 'W: tmpfile-not-regular-file /usr/lib/tmpfiles.d/symlink.conf' in out
