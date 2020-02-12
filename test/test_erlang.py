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


@pytest.mark.parametrize('package', ['binary/erlang'])
def test_erlang(tmpdir, package, erlangcheck):
    output, test = erlangcheck
    test.check(get_tested_package(package, tmpdir))
    out = output.print_results(output.results)
    assert 'E: beam-compiled-without-debuginfo /usr/lib/erlang/m.beam' in out
