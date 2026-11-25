import pytest
from rpmlint.checks.RubyCheck import RubyCheck
from rpmlint.filter import Filter

from Testing import CONFIG, get_tested_mock_package


@pytest.fixture(scope='function', autouse=True)
def rubycheck():
    CONFIG.info = True
    output = Filter(CONFIG)
    test = RubyCheck(CONFIG, output)
    yield output, test


@pytest.fixture
def output(rubycheck):
    output, _test = rubycheck
    yield output


@pytest.fixture
def test(rubycheck):
    _output, test = rubycheck
    yield test


@pytest.mark.parametrize('package', [get_tested_mock_package(
    files={
        # Good shebang
        '/usr/bin/good0.rb': {'content': '#!/usr/bin/ruby.ruby4.0'},
        '/usr/bin/good0': {'content': '#!/usr/bin/ruby.ruby4.0'},
        '/usr/bin/good1': {'content': '#!/usr/bin/ruby.ruby3.0\nputs "Hello world"'},
        '/usr/bin/good2': {'content': '#!/usr/bin/ruby.suffix -w\nputs "Hello world"'},
        '/usr/lib64/ruby/gems/4.0.0/gems/rbs-3.10.0/exe/rbs': {'content': '#!/usr/bin/env\nputs "Hello world"'},
        '/usr/lib64/ruby/gem.rb': {'content': '#!/usr/bin/env\nputs "Hello world"'},
        # Bad shebang
        '/usr/bin/bad1.rb': {'content': '#!/usr/bin/env ruby.ruby4.0'},
        '/usr/bin/bad2.rb': {'content': '#!/usr/bin/ruby'},
        '/usr/bin/bad3': {'content': '#!/usr/bin/ruby -w\nputs "Hello world"'},
        '/usr/bin/bad4': {'content': '#!/usr/bin/env ruby -w\nputs "Hello world"'},
        '/usr/bin/link': {
            'linkto': '/usr/lib64/ruby/gem.rb',
        },
    }
)])
def test_ruby_shebang(package, test, output):
    test.check(package)
    out = output.print_results(output.results)
    assert 'E: ruby-script-wrong-shebang /usr/bin/good0.rb' not in out
    assert 'E: ruby-script-wrong-shebang /usr/bin/good0' not in out
    assert 'E: ruby-script-wrong-shebang /usr/bin/good1' not in out
    assert 'E: ruby-script-wrong-shebang /usr/bin/good2' not in out

    assert 'E: ruby-script-wrong-shebang /usr/lib64/ruby/gems/4.0.0/gems/rbs-3.10.0/exe/rbs' not in out
    assert 'E: ruby-script-wrong-shebang /usr/lib64/ruby/bad.rb' not in out

    assert 'E: ruby-script-wrong-shebang /usr/bin/bad1.rb' in out
    assert 'E: ruby-script-wrong-shebang /usr/bin/bad2.rb' in out
    assert 'E: ruby-script-wrong-shebang /usr/bin/bad3' in out
    assert 'E: ruby-script-wrong-shebang /usr/bin/bad4' in out
    assert 'E: ruby-script-wrong-shebang /usr/bin/link' in out
