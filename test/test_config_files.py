from mockdata.mock_config_files import (
    ConfigFilesBrokenPackage,
    ConfigFilesOkPackage,
)
from mockdata.mock_logrotate import LogrotatePackage
import pytest
from rpmlint.checks.ConfigFilesCheck import ConfigFilesCheck
from rpmlint.filter import Filter

from Testing import CONFIG


@pytest.fixture(scope='function', autouse=True)
def configfilescheck():
    CONFIG.info = True
    output = Filter(CONFIG)
    test = ConfigFilesCheck(CONFIG, output)
    return output, test


@pytest.mark.parametrize('package', [ConfigFilesBrokenPackage])
def test_config_files1(package, configfilescheck):
    output, test = configfilescheck
    test.check(package)
    out = output.print_results(output.results)
    assert 'non-etc-or-var-file-marked-as-conffile /usr/share/conffile3' in out
    assert 'conffile-without-noreplace-flag /etc/conffile1' in out
    assert 'conffile-without-noreplace-flag /var/conffile2' in out
    assert 'conffile-without-noreplace-flag /usr/share/conffile3' in out


@pytest.mark.parametrize('package', [LogrotatePackage, ConfigFilesOkPackage])
def test_config_files_correct1(package, configfilescheck):
    output, test = configfilescheck
    test.check(package)
    out = output.print_results(output.results)
    assert 'non-etc-or-var-file-marked-as-conffile' not in out
    assert 'conffile-without-noreplace-flag' not in out
