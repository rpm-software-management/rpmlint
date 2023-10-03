import pytest
from rpmlint.checks.ZyppSyntaxCheck import ZyppSyntaxCheck
from rpmlint.filter import Filter

from Testing import CONFIG, get_tested_mock_package


@pytest.fixture(scope='function', autouse=True)
def zyppsyntaxcheck():
    CONFIG.info = True
    output = Filter(CONFIG)
    test = ZyppSyntaxCheck(CONFIG, output)
    return output, test


@pytest.fixture
def output(zyppsyntaxcheck):
    output, _test = zyppsyntaxcheck
    yield output


@pytest.fixture
def test(zyppsyntaxcheck):
    _output, test = zyppsyntaxcheck
    yield test


@pytest.mark.parametrize('package', [get_tested_mock_package(
    header={
        'requires': [
            'rpmlib(CompressedFileNames) <= 3.0.4-1',
            'rpmlib(FileDigests) <= 4.6.0-1',
            'rpmlib(PayloadFilesHavePrefix) <= 4.0-1',
            'rpmlib(PayloadIsXz) <= 5.2-1',
            'rpmlib(RichDependencies) <= 4.12.0-1',
        ],
        'supplements': ['packageand(c:d)'],
        'recommends': ['packageand(a:b)'],
        'suggests': ['(a and b)'],
        'conflicts': [
            'bee',
            'otherproviders(yast2_theme)',
        ],
    },
)])
def test_packageand(package, test, output):
    test.check(package)
    out = output.print_results(output.results)
    assert 'suse-zypp-packageand packageand(c:d)' in out
    assert 'suse-zypp-packageand packageand(a:b)' in out
    assert '(a and b)' not in out
    assert 'bee' not in out
    assert 'suse-zypp-otherproviders otherproviders(yast2_theme)' in out


@pytest.mark.parametrize('package', [get_tested_mock_package(
    header={
        'requires': [
            'rpmlib(CompressedFileNames) <= 3.0.4-1',
            'rpmlib(FileDigests) <= 4.6.0-1',
            'rpmlib(PayloadFilesHavePrefix) <= 4.0-1',
            'rpmlib(PayloadIsXz) <= 5.2-1',
            'rpmlib(RichDependencies) <= 4.12.0-1',
        ],
        'supplements': ['(c and d)'],
        'recommends': ['b'],
        'suggests': ['(a and b)'],
        'conflicts': [
            'bee',
        ],
    },
)])
def test_packageand_ok(package, test, output):
    test.check(package)
    out = output.print_results(output.results)
    assert 'suse-zypp-packageand' not in out
    assert 'suse-zypp-otherproviders' not in out
