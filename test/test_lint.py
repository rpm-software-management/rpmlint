from pathlib import Path

import pytest
from rpmlint.lint import Lint

from Testing import TEST_CONFIG, testpath

options_preset = {
    'config': TEST_CONFIG,
    'verbose': False,
    'strict': False,
    'permissive': False,
    'print_config': False,
    'explain': '',
    'rpmfile': '',
    'rpmlintrc': False,
    'installed': '',
    'time_report': False,
    'profile': False
}

basic_tests = [
    'AlternativesCheck',
    'AppDataCheck',
    'BinariesCheck',
    'BuildDateCheck',
    'BuildRootCheck',
    'ConfigFilesCheck',
    'DBusPolicyCheck',
    'DuplicatesCheck',
    'DocCheck',
    'ErlangCheck',
    'FHSCheck',
    'FilesCheck',
    'IconSizesCheck',
    'I18NCheck',
    'LogrotateCheck',
    'MenuCheck',
    'MenuXDGCheck',
    'MixedOwnershipCheck',
    'PkgConfigCheck',
    'PostCheck',
    'SignatureCheck',
    'SourceCheck',
    'SpecCheck',
    'TagsCheck',
    'ZipCheck',
    'ZyppSyntaxCheck',
]


def _remove_except_zip(dictionary):
    """
    In order to not lie in coverage redux the test run on the
    tests to just ZipCheck which has full coverage
    """
    redux = {}
    redux['ZipCheck'] = dictionary['ZipCheck']
    return redux


def test_cases_loading():
    linter = Lint(options_preset)
    assert list(linter.checks.keys()) == basic_tests


def test_configoutput(capsys):
    additional_options = {
        'print_config': True,
    }
    options = {**options_preset, **additional_options}
    linter = Lint(options)
    linter.run()
    out, err = capsys.readouterr()
    assert out
    assert 'Vendor = "Fedora Project"' in out
    assert 're.compile' not in out
    assert not err


def test_explain_unknown(capsys):
    message = ['bullcrap']
    additional_options = {
        'explain': message,
    }
    options = {**options_preset, **additional_options}
    linter = Lint(options)
    linter.run()
    out, err = capsys.readouterr()
    assert 'bullcrap:\nUnknown message' in out
    assert not err


def test_explain_known(capsys):
    message = ['infopage-not-compressed']
    additional_options = {
        'explain': message,
    }
    options = {**options_preset, **additional_options}
    linter = Lint(options)
    linter.run()
    out, err = capsys.readouterr()
    assert 'This info page is not compressed' in out
    assert 'Unknown message' not in out
    assert not err


def test_explain_with_unknown(capsys):
    message = ['infopage-not-compressed', 'blablablabla']
    additional_options = {
        'explain': message,
    }
    options = {**options_preset, **additional_options}
    linter = Lint(options)
    linter.run()
    out, err = capsys.readouterr()
    assert 'This info page is not compressed' in out
    assert 'Unknown message' in out
    assert not err


def test_explain_no_binary_from_cfg(capsys):
    """
    Test that 'explain' option can read updated description from configuration.

    Test 'no-binary' error that is defined in CheckBinaries.toml file by
    default and then it's overridden to the custom values defined in
    'descriptions.config' file.
    """
    additional_options = {
        'config': [testpath() / 'configs/descriptions.config'],
        'explain': ['no-binary']
    }
    options = {**options_preset, **additional_options}
    linter = Lint(options)
    linter.run()
    out, err = capsys.readouterr()

    # the new string is present and the old one is not
    assert 'A new text for no-binary error.' in out
    assert 'The package should be of the noarch architecture' not in out
    assert not err


def test_explain_non_standard_dir_from_cfg(capsys):
    """
    Test that 'explain' option can read updated description from configuration.

    Test 'non-standard-dir-in-usr' error that is special because the original
    description is not defined in FHSCheck.toml but in FHSCheck.py. Then it's
    supposed to be overridden to the custom values defined in
    'descriptions.config' file.
    """
    additional_options = {
        'config': [testpath() / 'configs/descriptions.config'],
        'explain': ['non-standard-dir-in-usr']
    }
    options = {**options_preset, **additional_options}
    linter = Lint(options)
    linter.run()
    out, err = capsys.readouterr()

    assert 'A new text for non-standard-dir-in-usr error.' in out
    assert 'Your package is creating a non-standard subdirectory in /usr' not in out
    assert not err


@pytest.mark.parametrize('packages', [Path('test/binary/non-fhs-0-0.x86_64.rpm')])
def test_descriptions_from_config(capsys, packages):
    """
    Test that rpmlint updates 'parametrized' descriptions from configuration.

    We test that "parametrized" errors (non-standard-dir-in-usr
    and non-standard-dir-in-var) were overridden by values from
    'descriptions.config' file.
    """
    additional_options = {
        'config': [testpath() / 'configs/descriptions.config'],
        'rpmfile': [packages]
    }
    options_preset['verbose'] = True
    options = {**options_preset, **additional_options}
    linter = Lint(options)
    linter.run()
    out, err = capsys.readouterr()

    assert 'A new text for non-standard-dir-in-usr error.' in out
    assert 'A new text for non-standard-dir-in-var error.' in out

    assert 'Your package is creating a non-standard subdirectory in /usr' \
           not in out
    assert 'Your package is creating a non-standard subdirectory in /var' \
           not in out
    assert not err


@pytest.mark.parametrize('packages', [Path('test/source/wrongsrc-0-0.src.rpm')])
def test_run_single(capsys, packages):
    additional_options = {
        'rpmfile': [packages],
    }
    options = {**options_preset, **additional_options}
    linter = Lint(options)
    linter.checks = _remove_except_zip(linter.checks)
    linter.run()
    out, err = capsys.readouterr()
    assert '1 packages and 0 specfiles checked' in out
    assert not err


@pytest.mark.parametrize('packages', [Path('test/source/wrongsrc-0-0.src.rpm')])
def test_run_installed(capsys, packages):
    # load up 1 normal path file and 2 installed packages
    additional_options = {
        'rpmfile': [packages],
        'installed': ['binutils', 'rpm'],
    }
    options = {**options_preset, **additional_options}
    linter = Lint(options)
    linter.checks = _remove_except_zip(linter.checks)
    linter.run()
    out, err = capsys.readouterr()
    assert '3 packages and 0 specfiles checked' in out
    assert not err


@pytest.mark.parametrize('packages', [Path('test/binary/ruby2.5-rubygem-rubyzip-testsuite-1.2.1-0.x86_64.rpm')])
def test_run_strict(capsys, packages):
    """
    Test if we convert warning to error
    """
    additional_options = {
        'rpmfile': [packages],
        'strict': True,
    }
    options = {**options_preset, **additional_options}
    linter = Lint(options)
    linter.checks = _remove_except_zip(linter.checks)
    linter.run()
    out, err = capsys.readouterr()
    assert 'W: unable-to-read-zip' not in out
    assert 'E: unable-to-read-zip' in out
    assert not err


def test_run_installed_not_present(capsys):
    additional_options = {
        'rpmfile': [],
        'installed': ['non-existing-package'],
    }
    options = {**options_preset, **additional_options}
    linter = Lint(options)
    linter.checks = _remove_except_zip(linter.checks)
    linter.run()
    out, err = capsys.readouterr()
    assert '0 packages and 0 specfiles checked' in out
    assert 'there is no installed rpm' in err
    assert 'There are no files to process' in err


def test_run_installed_and_no_files(capsys):
    additional_options = {
        'rpmfile': [],
        'installed': ['rpm'],
    }
    options = {**options_preset, **additional_options}
    linter = Lint(options)
    linter.checks = _remove_except_zip(linter.checks)
    linter.run()
    out, err = capsys.readouterr()
    assert '1 packages and 0 specfiles checked' in out
    assert not err


def test_header_information(capsys):
    additional_options = {
        'rpmfile': [],
        'installed': ['python3-rpm'],
    }
    options = {**options_preset, **additional_options}
    linter = Lint(options)
    linter.checks = _remove_except_zip(linter.checks)
    linter.run()
    out, err = capsys.readouterr()
    assert 'packages: 1' in out


@pytest.mark.parametrize('packages', [list(Path('test').glob('*/*.rpm'))])
@pytest.mark.parametrize('configs', [list(Path('configs').glob('*/*.toml'))])
@pytest.mark.no_cover
def test_run_full_rpm(capsys, packages, configs):
    number_of_pkgs = len(packages)
    additional_options = {
        'rpmfile': packages,
    }
    options_preset['config'] = configs
    options = {**options_preset, **additional_options}
    linter = Lint(options)
    linter.run()
    out, err = capsys.readouterr()
    assert f'{number_of_pkgs} packages and 0 specfiles checked' in out
    # we convert the err as we don't care about errors from missing
    # spellchecking dictionaries -> we have to ignore it
    err_reduced = [a for a in err.split('\n') if not a.startswith('(none): W: unable to load spellchecking dictionary for') and a != '']
    # also we can find out signatures are wrong because of the other distros
    # could've signed it
    err_reduced = [a for a in err_reduced if not a.startswith('Error checking signature of')]
    assert not err_reduced


@pytest.mark.parametrize('packages', [list(Path('test/spec').glob('*.spec'))])
@pytest.mark.parametrize('configs', [list(Path('configs').glob('*/*.toml'))])
@pytest.mark.no_cover
def test_run_full_specs(capsys, packages, configs):
    number_of_pkgs = len(packages)
    additional_options = {
        'rpmfile': packages,
    }
    options_preset['config'] = configs
    options = {**options_preset, **additional_options}
    linter = Lint(options)
    linter.run()
    out, err = capsys.readouterr()
    assert f'0 packages and {number_of_pkgs} specfiles checked' in out
    assert not err


@pytest.mark.parametrize('packages', [Path('test/spec')])
@pytest.mark.no_cover
def test_run_full_directory(capsys, packages):
    assert packages.is_dir()
    file_list = []
    for item in packages.iterdir():
        if item.is_file():
            file_list.append(item)
    number_of_pkgs = len(file_list)
    additional_options = {
        'rpmfile': [packages],
    }
    options = {**options_preset, **additional_options}
    linter = Lint(options)
    linter.run()
    out, err = capsys.readouterr()
    assert f'0 packages and {number_of_pkgs} specfiles checked' in out
    assert not err


def test_run_empty(capsys):
    linter = Lint(options_preset)
    linter.run()
    out, err = capsys.readouterr()
    assert err
    assert '0 packages and 0 specfiles checked; 0 errors, 0 warnings' in out


@pytest.mark.parametrize('packages', [Path('test/rpmlintrc/single')])
def test_run_rpmlintrc_single_dir(capsys, packages):
    additional_options = {
        'rpmfile': [packages],
    }
    options = {**options_preset, **additional_options}
    linter = Lint(options)
    linter.run()
    out, err = capsys.readouterr()
    assert not err
    assert 'rpmlintrc:' in out


@pytest.mark.parametrize('packages', [Path('test/rpmlintrc/multiple')])
def test_run_rpmlintrc_multiple(capsys, packages):
    additional_options = {
        'rpmfile': [packages],
    }
    options = {**options_preset, **additional_options}
    linter = Lint(options)
    linter.run()
    out, err = capsys.readouterr()
    assert 'rpmlintrc:' not in out
    assert 'There are multiple items to be loaded for rpmlintrc' in err
    assert '0 badness' in out


@pytest.mark.parametrize('packages', [Path('test/rpmlintrc/single/sample.spec')])
def test_run_rpmlintrc_single_file(capsys, packages):
    additional_options = {
        'rpmfile': [packages],
    }
    options = {**options_preset, **additional_options}
    linter = Lint(options)
    linter.run()
    out, err = capsys.readouterr()
    assert not err
    assert 'rpmlintrc:' in out
