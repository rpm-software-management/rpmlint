from mockdata.mock_logrotate import LogrotatePackage
import pytest
from rpmlint.checks.LogrotateCheck import LogrotateCheck
from rpmlint.filter import Filter

from Testing import CONFIG


@pytest.fixture(scope='function', autouse=True)
def logrotatecheck():
    CONFIG.info = True
    output = Filter(CONFIG)
    test = LogrotateCheck(CONFIG, output)
    return output, test


@pytest.mark.parametrize('package', [LogrotatePackage])
def test_logrotate(package, logrotatecheck):
    output, test = logrotatecheck
    test.check(package)
    out = output.print_results(output.results)
    lines = out.splitlines()
    assert 'E: logrotate-log-dir-not-packaged /var/log/myapp' in out
    # /var/log is owned by the filesystem package and must not be reported
    assert not any(line.endswith('E: logrotate-log-dir-not-packaged /var/log') for line in lines)
    assert 'E: logrotate-duplicate /var/log/myapp' in out
    assert 'E: logrotate-user-writable-log-dir /tmp/foo marxin:users 0755' in out
    assert 'E: logrotate-user-writable-log-dir /tmp/foo2 root:users2 0777' in out
