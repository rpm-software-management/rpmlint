from pathlib import PosixPath

import pytest
from rpmlint.cli import process_lint_args
from rpmlint.config import Config
from rpmlint.lint import Lint


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


@pytest.mark.parametrize('test_arguments', [['-c', 'configs/openSUSE']])
def test_parsing_opensuse_conf(test_arguments):
    parsed = process_lint_args(test_arguments)

    assert len(parsed['config']) == 7
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
