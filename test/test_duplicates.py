import pytest
from rpmlint.checks.DuplicatesCheck import DuplicatesCheck
from rpmlint.filter import Filter

from Testing import CONFIG, get_tested_package


@pytest.fixture(scope='function', autouse=True)
def duplicatescheck():
    CONFIG.info = True
    output = Filter(CONFIG)
    test = DuplicatesCheck(CONFIG, output)
    return output, test


@pytest.mark.parametrize('package', ['binary/duplicates'])
def test_duplicates(tmpdir, package, duplicatescheck):
    output, test = duplicatescheck
    test.check(get_tested_package(package, tmpdir))
    out = output.print_results(output.results)

    assert 'E: hardlink-across-partition /var/foo /etc/foo' in out
    assert 'E: hardlink-across-config-files /var/foo2 /etc/foo2' in out
    assert 'W: files-duplicate /etc/bar3 /etc/bar:/etc/bar2' in out
    assert 'W: files-duplicate /etc/strace2.txt /etc/strace1.txt' in out
    assert 'E: files-duplicated-waste 270516' in out


@pytest.mark.parametrize('package', ['binary/bad-crc-uncompressed'])
def test_duplicates_correct(tmpdir, package, duplicatescheck):
    output, test = duplicatescheck
    test.check(get_tested_package(package, tmpdir))
    out = output.print_results(output.results)

    assert 'E: hardlink-across-partition' not in out
    assert 'E: hardlink-across-config-files' not in out
    assert 'W: files-duplicate' not in out
    assert 'E: files-duplicated-waste' not in out
