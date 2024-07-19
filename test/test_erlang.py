from importlib.metadata import distribution

from mockdata.mock_erlang import ERLANG
from packaging.version import parse
import pytest
from rpmlint.checks.ErlangCheck import ErlangCheck
from rpmlint.filter import Filter

from Testing import CONFIG


@pytest.fixture(scope='function', autouse=True)
def erlangcheck():
    CONFIG.info = True
    output = Filter(CONFIG)
    test = ErlangCheck(CONFIG, output)
    return output, test


@pytest.mark.skipif(parse(distribution('pybeam').version) < parse('0.7'), reason='pybeam >= 0.7 required')
@pytest.mark.parametrize('package', [ERLANG])
def test_erlang(package, erlangcheck):
    output, test = erlangcheck
    test.check(package)
    out = output.print_results(output.results)
    assert 'E: beam-compiled-without-debuginfo /usr/lib/erlang/m.beam' in out
    assert 'W: beam-compile-info-missed /usr/lib/erlang/m-no-CInf.beam' in out
