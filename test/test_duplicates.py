from mockdata.mock_duplicates import (
    HardlinksAndDuplicatesPresent,
    NoHardLinksAndDuplicatesPresent
)
import pytest
from rpmlint.checks.DuplicatesCheck import DuplicatesCheck
from rpmlint.filter import Filter

from Testing import CONFIG


@pytest.fixture(scope='function', autouse=True)
def duplicatescheck():
    CONFIG.info = True
    output = Filter(CONFIG)
    test = DuplicatesCheck(CONFIG, output)
    yield output, test


@pytest.fixture()
def test(duplicatescheck):
    _output, test = duplicatescheck
    yield test


@pytest.fixture()
def output(duplicatescheck):
    output, _test = duplicatescheck
    yield output


@pytest.mark.parametrize('package', [HardlinksAndDuplicatesPresent])
def test_duplicates1(package, test, output):
    test.check(package)
    out = output.print_results(output.results)

    assert 'E: hardlink-across-partition /var/foo /etc/foo' in out
    assert 'E: hardlink-across-config-files /var/foo2 /etc/foo2' in out
    assert 'W: files-duplicate /etc/bar3 /etc/bar:/etc/bar2' in out
    assert 'W: files-duplicate /etc/strace2.txt /etc/strace1.txt' in out
    assert 'W: files-duplicate /etc/small2 /etc/small' not in out
    assert 'E: files-duplicated-waste 270543' in out


@pytest.mark.parametrize('package', [NoHardLinksAndDuplicatesPresent])
def test_duplicates_correct(package, test, output):
    test.check(package)
    out = output.print_results(output.results)

    assert 'E: hardlink-across-partition' not in out
    assert 'E: hardlink-across-config-files' not in out
    assert 'W: files-duplicate' not in out
    assert 'E: files-duplicated-waste' not in out
