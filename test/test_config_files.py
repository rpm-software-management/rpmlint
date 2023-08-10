import pytest
from rpmlint.checks.ConfigFilesCheck import ConfigFilesCheck
from rpmlint.filter import Filter

from Testing import CONFIG, get_tested_mock_package


@pytest.fixture(scope='function', autouse=True)
def configfilescheck():
    CONFIG.info = True
    output = Filter(CONFIG)
    test = ConfigFilesCheck(CONFIG, output)
    return output, test


@pytest.mark.parametrize('package', [get_tested_mock_package(
    files={
        '/etc/conffile1': {'content': '# Conffile1', 'metadata': {'flags': 1}},
        '/var/conffile2': {'content': '# Conffile2', 'metadata': {'flags': 1}},
        '/usr/share/conffile3': {'content': '# Conffile3', 'metadata': {'flags': 1}},
    }
)])
def test_config_files1(package, configfilescheck):
    output, test = configfilescheck
    test.check(package)
    out = output.print_results(output.results)
    assert 'non-etc-or-var-file-marked-as-conffile /usr/share/conffile3' in out
    assert 'conffile-without-noreplace-flag /etc/conffile1' in out
    assert 'conffile-without-noreplace-flag /var/conffile2' in out
    assert 'conffile-without-noreplace-flag /usr/share/conffile3' in out


@pytest.mark.parametrize('package', [get_tested_mock_package(
    files={
        'tmp/foo/my.log': {'content': '', 'metadata': {'flags': 0}},
        'tmp/foo2': {'content': '', 'metadata': {'flags': 0}},
        'tmp/foo2/my.log': {'content': '', 'metadata': {'flags': 0}},
        'etc/logrotate.d': {'content': '', 'metadata': {'flags': 0}},
        'etc/logrotate.d/logrotate2.conf': {'content': '', 'metadata': {'flags': 0}},
        'etc/logrotate.d/logrotate.conf': {'content': '', 'metadata': {'flags': 0}},
    }
)])
def test_config_files_correct1(package, configfilescheck):
    output, test = configfilescheck
    test.check(package)
    out = output.print_results(output.results)
    assert 'non-etc-or-var-file-marked-as-conffile' not in out
    assert 'conffile-without-noreplace-flag' not in out
