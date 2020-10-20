from pathlib import PosixPath

import pytest
from rpmlint.cli import process_lint_args


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

    assert len(parsed['config']) == 3
    assert PosixPath('configs/openSUSE/opensuse.toml') in parsed['config']
    assert PosixPath('configs/openSUSE/licenses.toml') in parsed['config']
    assert PosixPath('configs/openSUSE/pie-executables.toml') in parsed['config']
