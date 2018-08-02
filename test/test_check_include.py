from rpmlint.Filter import Filter
from rpmlint.SpecCheck import SpecCheck

from Testing import CONFIG, get_tested_package


def test_check_include():
    CONFIG.info = True
    output = Filter(CONFIG)
    test = SpecCheck(CONFIG, output)
    test.check_source(get_tested_package('source/CheckInclude'))
    out = output.print_results(output.results)
    assert 'no-buildroot-tag' in out
    assert 'E: specfile-error error: query of specfile' not in out
