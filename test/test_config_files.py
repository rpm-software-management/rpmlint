import pytest
from rpm import RPMFILE_CONFIG, RPMFILE_NOREPLACE
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
        '/etc/conffile1': {'metadata': {'flags': RPMFILE_CONFIG}},
        '/var/conffile2': {'metadata': {'flags': RPMFILE_CONFIG}},
        '/usr/share/conffile3': {'metadata': {'flags': RPMFILE_CONFIG}},
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


@pytest.mark.parametrize('package', [
    get_tested_mock_package(
        files=[
            'tmp/foo/my.log',
            'tmp/foo2/my.log',
            'etc/logrotate.d/logrotate2.conf',
            'etc/logrotate.d/logrotate.conf',
        ]
    ),
    get_tested_mock_package(
        files={
            '/etc/conffile1': {'metadata': {'flags': RPMFILE_CONFIG & RPMFILE_NOREPLACE}},
            '/var/conffile2': {'metadata': {'flags': RPMFILE_CONFIG & RPMFILE_NOREPLACE}},
        }
    )
])
def test_config_files_correct1(package, configfilescheck):
    output, test = configfilescheck
    test.check(package)
    out = output.print_results(output.results)
    assert 'non-etc-or-var-file-marked-as-conffile' not in out
    assert 'conffile-without-noreplace-flag' not in out
