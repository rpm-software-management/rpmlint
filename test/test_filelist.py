import pytest
from rpmlint.checks.FilelistCheck import FilelistCheck
from rpmlint.filter import Filter

from Testing import CONFIG, get_tested_package


@pytest.fixture(scope='function', autouse=True)
def filelistcheck():
    CONFIG.info = True
    output = Filter(CONFIG)
    test = FilelistCheck(CONFIG, output)
    return output, test


@pytest.mark.parametrize('package', ['binary/filelist'])
def test_filelist(tmpdir, package, filelistcheck):
    output, test = filelistcheck
    test.check(get_tested_package(package, tmpdir))
    out = output.print_results(output.results)
    assert 'E: filelist-forbidden-sysconfig /etc/rc.config.d/foo.config' in out
    assert 'E: filelist-forbidden /var/adm/setup' in out
    assert 'E: filelist-forbidden-perl-dir /usr/lib/perl5/site_perl/x.pl' in out
    assert 'E: filelist-forbidden-python-test-dir /usr/lib/python/site-packages/tests' in out
    assert 'E: filelist-forbidden-backup-file /foo~' in out
    assert 'E: filelist-forbidden-devel-in-lib /lib64/x.a' in out
    assert 'E: filelist-forbidden-devel-in-lib /lib64/y.so' in out
    assert 'E: filelist-forbidden-fhs23 /etc/X11/app-defaults/foo' in out
    assert 'E: filelist-forbidden-yast2 /usr/lib/YaST2/x.ycp' in out
    assert 'E: filelist-forbidden-srv /usr/local/ftp' in out
    assert 'E: filelist-forbidden-games /usr/games/bin' in out
    assert 'E: filelist-forbidden-debuginfo /usr/lib/debug/foo.debug' in out
    assert 'E: filelist-forbidden-opt /opt/gnome' in out
