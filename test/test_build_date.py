import re

import pytest
from rpmlint.checks.BuildDateCheck import BuildDateCheck
from rpmlint.filter import Filter

from Testing import CONFIG, get_tested_package


@pytest.fixture(scope='function', autouse=True)
def builddatecheck():
    CONFIG.info = True
    output = Filter(CONFIG)
    test = BuildDateCheck(CONFIG, output)
    return output, test


@pytest.mark.parametrize('package', ['binary/builddate'])
def test_build_date_time(tmpdir, package, builddatecheck):
    output, test = builddatecheck
    test.istoday = re.compile('Jan  1 2019')
    test.check(get_tested_package(package, tmpdir))
    out = output.print_results(output.results)
    assert 'E: file-contains-date-and-time /bin/with-datetime' in out
    assert 'E: file-contains-current-date /bin/with-date' in out


@pytest.mark.parametrize('package', ['binary/bashisms'])
def test_build_date_time_correct(tmpdir, package, builddatecheck):
    output, test = builddatecheck
    test.istoday = re.compile('Jan  1 2019')
    test.check(get_tested_package(package, tmpdir))
    out = output.print_results(output.results)
    assert 'E: file-contains-date-and-time' not in out
    assert 'E: file-contains-current-date' not in out
