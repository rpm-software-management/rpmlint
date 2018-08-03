import pytest
from rpmlint.checks.RpmFileCheck import RpmFileCheck
from rpmlint.Filter import Filter

from Testing import CONFIG, get_tested_package


@pytest.fixture(scope='function', autouse=True)
def rpmfilescheck():
    CONFIG.info = True
    output = Filter(CONFIG)
    test = RpmFileCheck(CONFIG, output)
    return output, test


@pytest.mark.parametrize('package', ['binary/apache-commons-collections-testframework-javadoc'])
def test_distribution_tags(tmpdir, package):
    output, test = rpmfilescheck()
    test.check(get_tested_package(package, tmpdir))
    out = output.print_results(output.results)
    assert 'filename-too-long-for-joliet' in out
    assert 'filename is too long to fit on a joliet filesystem' in out
