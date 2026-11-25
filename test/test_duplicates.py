from mockdata.mock_duplicates import (
    CrossPrefixDuplicates,
    HardlinksAndDuplicatesPresent,
    MixedHardlinksAndDuplicates,
    NoHardLinksAndDuplicatesPresent,
    PureDuplicates,
    PureHardlinksAcrossPartition
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


@pytest.mark.parametrize('package', [MixedHardlinksAndDuplicates])
def test_duplicates_mixed_hardlinks_cross_prefix_suppressed(package, test, output):
    # two files hardlinked across prefixes plus one genuine duplicate:
    # the hardlink across prefixes is reported, but files-duplicate stays
    # suppressed because the duplicates span different prefixes and can
    # not be hardlinked anyway
    test.check(package)
    out = output.print_results(output.results)

    assert 'E: hardlink-across-partition /var/dup_b /etc/dup_a' in out
    assert 'W: files-duplicate' not in out
    assert 'E: files-duplicated-waste' not in out


@pytest.mark.parametrize('package', [CrossPrefixDuplicates])
def test_duplicates_cross_prefix_suppressed(package, test, output):
    # genuine duplicates in different prefixes can not be hardlinked,
    # so files-duplicate is not reported for them
    test.check(package)
    out = output.print_results(output.results)

    assert 'W: files-duplicate' not in out
    assert 'E: hardlink-across-partition' not in out
    assert 'E: files-duplicated-waste' not in out


@pytest.mark.parametrize('package', [PureHardlinksAcrossPartition])
def test_duplicates_pure_hardlinks_across_partition(package, test, output):
    # only hardlinks across prefixes: no genuine duplicates to report
    test.check(package)
    out = output.print_results(output.results)

    assert 'E: hardlink-across-partition /var/linked /etc/linked' in out
    assert 'W: files-duplicate' not in out
    assert 'E: files-duplicated-waste' not in out


@pytest.mark.parametrize('package', [PureDuplicates])
def test_duplicates_pure_duplicates(package, test, output):
    # only genuine duplicates: no hardlinks involved at all
    test.check(package)
    out = output.print_results(output.results)

    assert 'W: files-duplicate /etc/only_b /etc/only_a' in out
    assert 'E: hardlink-across-partition' not in out
    assert 'E: hardlink-across-config-files' not in out
    assert 'E: files-duplicated-waste' not in out
