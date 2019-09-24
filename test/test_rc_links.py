import pytest
from rpmlint.checks.RCLinksCheck import RCLinksCheck
from rpmlint.filter import Filter

from Testing import CONFIG, get_tested_package


@pytest.fixture(scope='function', autouse=True)
def rclinkscheck():
    CONFIG.info = True
    output = Filter(CONFIG)
    test = RCLinksCheck(CONFIG, output)
    return output, test


@pytest.mark.parametrize('package', ['binary/rc-links'])
def test_bashisms(tmpdir, package, rclinkscheck):
    output, test = rclinkscheck
    test.check(get_tested_package(package, tmpdir))
    out = output.print_results(output.results)
    assert 'W: missing-rclink foo' in out
    assert 'E: systemd-shadowed-initscript bar' in out
