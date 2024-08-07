import pytest
from rpmlint.checks.LogrotateCheck import LogrotateCheck
from rpmlint.filter import Filter

from Testing import CONFIG, get_tested_mock_package


@pytest.fixture(scope='function', autouse=True)
def logrotatecheck():
    CONFIG.info = True
    output = Filter(CONFIG)
    test = LogrotateCheck(CONFIG, output)
    return output, test


@pytest.mark.parametrize('package', [get_tested_mock_package(
files={
'/etc/logrotate.d/logrotate.conf': {
    'content': '''/var/log/myapp/*.log {
    su appuser appuser
    weekly
    rotate 4
    compress

    delaycompress
    missingok
    create 644 appuser appuser
}

/var/log/myapp/*.log {
    su appuser2 appuser2
}
'''
},
'/etc/logrotate.d/logrotate2.conf': {
    'content': '''/var/log/myapp/*.log {
    su appuser2 appuser2
}

/tmp/foo/my.log {
    # comment
    su appuser2 appuser2
}

/tmp/foo2/my.log {
    su appuser2 appuser2
}
'''
},
'/tmp/foo': {'is_dir': True, 'metadata': {'mode': 0o755, 'user': 'marxin', 'group': 'users'}},
'/tmp/foo/my.log': {'metadata': {'mode': 0o644, 'user': 'marxin', 'group': 'users'}},
'/tmp/foo2': {'is_dir': True, 'metadata': {'mode': 0o777, 'user': 'root', 'group': 'users2'}},
'/tmp/foo2/my.log': {'metadata': {'mode': 0o777, 'user': 'root', 'group': 'users2'}},
})])
def test_logrotate(package, logrotatecheck):
    output, test = logrotatecheck
    test.check(package)
    out = output.print_results(output.results)
    assert 'E: logrotate-log-dir-not-packaged /var/log/myapp' in out
    assert 'E: logrotate-duplicate /var/log/myapp' in out
    assert 'E: logrotate-user-writable-log-dir /tmp/foo marxin:users 0755' in out
    assert 'E: logrotate-user-writable-log-dir /tmp/foo2 root:users2 0777' in out
