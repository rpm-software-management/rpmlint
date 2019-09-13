import pytest
from rpmlint.checks.ConfigFilesCheck import ConfigFilesCheck
from rpmlint.filter import Filter

from Testing import CONFIG, get_tested_package


@pytest.fixture(scope='function', autouse=True)
def configfilescheck():
    CONFIG.info = True
    output = Filter(CONFIG)
    test = ConfigFilesCheck(CONFIG, output)
    return output, test


@pytest.mark.parametrize('package', ['binary/config-files'])
def test_config_files(tmpdir, package, configfilescheck):
    output, test = configfilescheck
    test.check(get_tested_package(package, tmpdir))
    out = output.print_results(output.results)
    assert 'non-etc-or-var-file-marked-as-conffile /usr/share/conffile3' in out
    assert 'conffile-without-noreplace-flag /etc/conffile1' in out
    assert 'conffile-without-noreplace-flag /var/conffile2' in out
    assert 'conffile-without-noreplace-flag /usr/share/conffile3' in out


@pytest.mark.parametrize('package', ['binary/logrotate'])
def test_config_files_correct(tmpdir, package, configfilescheck):
    output, test = configfilescheck
    test.check(get_tested_package(package, tmpdir))
    out = output.print_results(output.results)
    assert 'non-etc-or-var-file-marked-as-conffile' not in out
    assert 'conffile-without-noreplace-flag' not in out
