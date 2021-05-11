from pkg_resources import get_distribution, parse_version
import pytest
from rpmlint.checks.ErlangCheck import ErlangCheck
from rpmlint.filter import Filter

from Testing import CONFIG, get_tested_package


@pytest.fixture(scope='function', autouse=True)
def erlangcheck():
    CONFIG.info = True
    output = Filter(CONFIG)
    test = ErlangCheck(CONFIG, output)
    return output, test


@pytest.mark.skipif(get_distribution('pybeam').parsed_version < parse_version('0.7'), reason='pybeam >= 0.7 required')
@pytest.mark.parametrize('package', ['binary/erlang-test'])
def test_erlang(tmpdir, package, erlangcheck):
    output, test = erlangcheck
    test.check(get_tested_package(package, tmpdir))
    out = output.print_results(output.results)
    assert 'E: beam-compiled-without-debuginfo /usr/lib/erlang/m.beam' in out
    assert 'W: beam-compile-info-missed /usr/lib/erlang/m-no-CInf.beam' in out
