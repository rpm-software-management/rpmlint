import re

from mockdata.mock_build_date import BuildDatePackage
from mockdata.mock_bashisms import BashismsPackage
import pytest
from rpmlint.checks.BuildRootAndDateCheck import BuildRootAndDateCheck
from rpmlint.filter import Filter

from Testing import CONFIG


@pytest.fixture(scope='function', autouse=True)
def builddatecheck():
    CONFIG.info = True
    output = Filter(CONFIG)
    test = BuildRootAndDateCheck(CONFIG, output)
    return output, test


@pytest.mark.parametrize('package', [BuildDatePackage])
def test_build_date_time(package, builddatecheck):
    output, test = builddatecheck
    test.istoday = re.compile('Jan  1 2019')
    test.check(package)
    out = output.print_results(output.results)
    assert 'E: file-contains-date-and-time /bin/with-datetime' in out
    assert 'E: file-contains-current-date /bin/with-date' in out


@pytest.mark.parametrize('package', [BashismsPackage])
def test_build_date_time_correct(package, builddatecheck):
    output, test = builddatecheck
    test.istoday = re.compile('Jan  1 2019')
    test.check(package)
    out = output.print_results(output.results)
    assert 'E: file-contains-date-and-time' not in out
    assert 'E: file-contains-current-date' not in out
