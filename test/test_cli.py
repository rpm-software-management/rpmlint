from pathlib import PosixPath
from unittest.mock import Mock

import pytest
from rpmlint.cli import process_lint_args
from rpmlint.config import Config
from rpmlint.lint import Lint

from Testing import HAS_CHECKBASHISMS, HAS_DASH, HAS_RPMDB


@pytest.mark.parametrize('test_arguments', [['-c', 'rpmlint/configs/thisdoesntexist.toml']])
def test_parsing_non_existing_config_file(test_arguments):
    with pytest.raises(SystemExit) as exc:
        process_lint_args(test_arguments)
    assert exc.value.code == 2


@pytest.mark.parametrize('test_arguments', [['-c', 'rpmlint/configdefaults.toml']])
def test_parsing_config_file(test_arguments):
    parsed = process_lint_args(test_arguments)

    assert len(parsed['config']) == 1
    assert parsed['config'][0] == PosixPath('rpmlint/configdefaults.toml')


@pytest.mark.skipif(not HAS_CHECKBASHISMS, reason='Optional dependency checkbashisms not installed')
@pytest.mark.skipif(not HAS_DASH, reason='Optional dependency dash not installed')
@pytest.mark.parametrize('test_arguments', [['-c', 'configs/openSUSE']])
def test_parsing_opensuse_conf(test_arguments):
    parsed = process_lint_args(test_arguments)

    assert PosixPath('configs/openSUSE/opensuse.toml') in parsed['config']
    assert PosixPath('configs/openSUSE/licenses.toml') in parsed['config']
    assert PosixPath('configs/openSUSE/pie-executables.toml') in parsed['config']

    defaultcfg = Config()
    lint = Lint(parsed)
    default_checks = defaultcfg.configuration['Checks']
    checks = lint.config.configuration['Checks']
    # Verify that all original Checks are enabled and some new are added
    for check in default_checks:
        assert check in checks
    assert len(checks) > len(default_checks)

    # Verify that all scoring keys are a known checks
    checks = set(lint.output.error_details.keys())
    checks |= set(defaultcfg.configuration['Descriptions'].keys())

    score_keys = lint.config.configuration['Scoring'].keys()
    for score_key in score_keys:
        if score_key.startswith('percent-in-'):
            continue
        assert score_key in checks


@pytest.mark.skipif(not HAS_CHECKBASHISMS, reason='Optional dependency checkbashisms not installed')
@pytest.mark.skipif(not HAS_DASH, reason='Optional dependency dash not installed')
@pytest.mark.parametrize('test_arguments', [['-c', 'configs/Fedora']])
def test_parsing_fedora_conf(test_arguments):
    parsed = process_lint_args(test_arguments)

    assert len(parsed['config']) == 5
    assert PosixPath('configs/Fedora/fedora.toml') in parsed['config']
    assert PosixPath('configs/Fedora/licenses.toml') in parsed['config']
    assert PosixPath('configs/Fedora/users-groups.toml') in parsed['config']

    defaultcfg = Config()
    lint = Lint(parsed)
    default_checks = defaultcfg.configuration['Checks']
    checks = lint.config.configuration['Checks']
    # Verify that all original Checks are enabled and some new are added
    for check in default_checks:
        assert check in checks
    assert len(checks) > len(default_checks)

    # Verify that all scoring keys are a known checks
    checks = set(lint.output.error_details.keys())
    checks |= set(defaultcfg.configuration['Descriptions'].keys())

    score_keys = lint.config.configuration['Scoring'].keys()
    for score_key in score_keys:
        if score_key.startswith('percent-in-'):
            continue
        assert score_key in checks


def test_reset_check():
    files = ['test/spec/SpecCheck2.spec', 'test/spec/SpecCheck3.spec']
    options = process_lint_args(['--checks', 'SpecCheck'] + files)
    lint = Lint(options)
    lint.run()
    out = lint.output.print_results(lint.output.results, lint.config)
    assert 'more-than-one-%changelog-section' not in out


@pytest.mark.skipif(not HAS_RPMDB, reason='No RPM database present')
@pytest.mark.parametrize('args', [
    ['test/spec/SpecCheck2.spec', 'test/spec/SpecCheck3.spec'],
    ['-i', 'rpm', 'glibc'],
    ['test/spec/SpecCheck2.spec', '-i', 'rpm'],
    ['test/spec/SpecCheck2.spec', 'test/spec/SpecCheck3.spec', '-i', 'rpm', 'glibc'],
])
def test_validate_filters(args):
    options = process_lint_args(args)
    lint = Lint(options)
    lint.output.validate_filters = Mock(wraps=lint.output.validate_filters)
    lint.run()
    lint.output.validate_filters.assert_called_once()
