from mockdata.mock_bashisms import BashismsPackage
import pytest
from rpmlint.checks.BashismsCheck import BashismsCheck
from rpmlint.filter import Filter

from Testing import CONFIG, HAS_CHECKBASHISMS, HAS_DASH


@pytest.fixture(scope='function', autouse=True)
def bashismscheck():
    CONFIG.info = True
    output = Filter(CONFIG)
    test = BashismsCheck(CONFIG, output)
    return output, test


@pytest.mark.skipif(not HAS_CHECKBASHISMS, reason='Optional dependency checkbashisms not installed')
@pytest.mark.skipif(not HAS_DASH, reason='Optional dependency dash not installed')
@pytest.mark.parametrize('package', [BashismsPackage])
def test_bashisms(package, bashismscheck):
    output, test = bashismscheck
    test.check(package)
    out = output.print_results(output.results)
    assert 'W: potential-bashisms /bin/script1' in out
    assert 'W: bin-sh-syntax-error /bin/script2' in out


@pytest.mark.skipif(not HAS_CHECKBASHISMS, reason='Optional dependency checkbashisms not installed')
@pytest.mark.skipif(not HAS_DASH, reason='Optional dependency dash not installed')
@pytest.mark.parametrize('package', [BashismsPackage])
def test_bashisms_error(package, bashismscheck):
    output, test = bashismscheck
    package.dirname = 'I-do-not-exist-for-sure'

    with pytest.raises(FileNotFoundError):
        test.check(package)
