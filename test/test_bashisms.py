import pytest
from rpmlint.checks.BashismsCheck import BashismsCheck
from rpmlint.filter import Filter

from Testing import CONFIG, get_tested_package


@pytest.fixture(scope='function', autouse=True)
def bashismscheck():
    CONFIG.info = True
    output = Filter(CONFIG)
    test = BashismsCheck(CONFIG, output)
    return output, test


@pytest.mark.parametrize('package', ['binary/bashisms'])
def test_bashisms(tmpdir, package, bashismscheck):
    output, test = bashismscheck
    test.check(get_tested_package(package, tmpdir))
    out = output.print_results(output.results)
    assert 'W: potential-bashisms /bin/script1' in out
    assert 'W: bin-sh-syntax-error /bin/script2' in out


@pytest.mark.parametrize('package', ['binary/bashisms'])
def test_bashisms_error(tmpdir, package, bashismscheck):
    output, test = bashismscheck
    package = get_tested_package(package, tmpdir)
    package.dirname = 'I-do-not-exist-for-sure'
    with pytest.raises(FileNotFoundError):
        test.check(package)
