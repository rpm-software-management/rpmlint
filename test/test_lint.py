from pathlib import Path
import shutil

import pytest
from rpmlint.lint import Lint
from rpmlint.spellcheck import ENCHANT

from Testing import (
    get_tested_path, HAS_CHECKBASHISMS, HAS_DASH, HAS_ENGLISH_DICTIONARY, HAS_RPMDB,
    TEST_CONFIG
)

TEST_RPMLINTRC = get_tested_path('configs/testing2-rpmlintrc')

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
    'ignore_unused_rpmlintrc': False,
    'checks': None,
    'jobs': 1,
}

basic_tests = [
    'AlternativesCheck',
    'AppDataCheck',
    'BinariesCheck',
    'BuildRootAndDateCheck',
    'ConfigFilesCheck',
    'DBusPolicyCheck',
    'DuplicatesCheck',
    'DocCheck',
    'ErlangCheck',
    'FHSCheck',
    'FilesCheck',
    'IconSizesCheck',
    'I18NCheck',
    'LibraryDependencyCheck',
    'LogrotateCheck',
    'MenuCheck',
    'MenuXDGCheck',
    'MixedOwnershipCheck',
    'PkgConfigCheck',
    'PostCheck',
    'PythonCheck',
    'SELinuxIndependentModuleCheck',
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
    return {'ZipCheck': dictionary['ZipCheck']}


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


def test_time_report(capsys):
    additional_options = {
        'time_report': True,
    }
    options = {**options_preset, **additional_options}
    linter = Lint(options)
    linter.run()
    out, err = capsys.readouterr()
    assert out
    assert 'Duration' in out
    assert 'TOTAL' in out


@pytest.mark.parametrize('jobs', (1, 2))
def test_fatal_error_does_not_abort_run(tmp_path, capsys, jobs):
    """
    A fatal error in one package is reported as an E-level message and
    the run continues with the remaining packages, like other linters
    handle per-file fatal errors. The run still fails with exit code 3.
    """
    broken_before = tmp_path / 'aaa-broken.rpm'
    broken_before.write_bytes(b'not an rpm')
    broken_after = tmp_path / 'zzz-broken.rpm'
    broken_after.write_bytes(b'not an rpm either')
    # the healthy package sorts between the two broken ones so its
    # issues are reported after the first fatal error
    healthy = tmp_path / 'mmm-healthy.rpm'
    shutil.copy(get_tested_path('binary/binary-in-etc-1.0-0.x86_64.rpm'), healthy)
    additional_options = {
        'rpmfile': [broken_before, healthy, broken_after],
        'jobs': jobs,
    }
    options = {**options_preset, **additional_options}
    linter = Lint(options)
    assert linter.run() == 3
    out, err = capsys.readouterr()
    # both fatal errors are reported ...
    assert err.count('fatal error while reading') == 2
    assert 'aaa-broken.rpm' in err
    assert 'zzz-broken.rpm' in err
    # ... the healthy package is still fully reported ...
    assert 'binary-in-etc.x86_64: E: no-signature' in out
    # ... and the run ends with the usual summary
    assert '3 packages and 0 specfiles checked' in out


def test_fatal_error_identical_sequential_parallel(tmp_path, capsys):
    """
    Sequential and parallel runs report fatal errors identically.
    """
    import re
    broken = tmp_path / 'broken.rpm'
    broken.write_bytes(b'not an rpm')
    healthy = tmp_path / 'healthy.rpm'
    shutil.copy(get_tested_path('binary/binary-in-etc-1.0-0.x86_64.rpm'), healthy)
    outputs = []
    for jobs in (1, 2):
        additional_options = {
            'rpmfile': [broken, healthy],
            'jobs': jobs,
        }
        options = {**options_preset, **additional_options}
        linter = Lint(options)
        assert linter.run() == 3
        outputs.append(capsys.readouterr())

    # durations and temporary extraction paths vary between runs
    def normalize(s):
        s = re.sub(r'has taken [\d.]+ s', 'has taken X s', s)
        return re.sub(r'/tmp/rpmlint\.[^/:\s]+/', '/tmp/rpmlint.XXX/', s)
    assert normalize(outputs[0].out) == normalize(outputs[1].out)
    assert normalize(outputs[0].err) == normalize(outputs[1].err)


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


@pytest.mark.parametrize('configs', [
    # Message defined in configs/Fedora/warn-on-functions.toml
    (Path('configs/Fedora/warn-on-functions.toml'), False),
    (Path('configs/Fedora/scoring.toml'), True),
])
def test_explain_known_warn_on_function(capsys, configs):
    extraconfig, unknown = configs
    message = ['crypto-policy-non-compliance-openssl']
    additional_options = {
        'explain': message,
        'config': [extraconfig],
    }
    options = {**options_preset, **additional_options}
    linter = Lint(options)
    linter.run()
    out, err = capsys.readouterr()

    assert ('Unknown message' in out) == unknown
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
        'config': [get_tested_path('configs/descriptions.config')],
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
        'config': [get_tested_path('configs/descriptions.config')],
        'explain': ['non-standard-dir-in-usr']
    }
    options = {**options_preset, **additional_options}
    linter = Lint(options)
    linter.run()
    out, err = capsys.readouterr()

    assert 'A new text for non-standard-dir-in-usr error.' in out
    assert 'Your package is creating a non-standard subdirectory in /usr' not in out
    assert not err


@pytest.mark.skipif(not ENCHANT, reason='Optional dependency pyenchant not install')
@pytest.mark.skipif(not HAS_ENGLISH_DICTIONARY, reason='Missing English dictionary')
@pytest.mark.parametrize('packages', [Path('test/binary/non-fhs-0-0.x86_64.rpm')])
def test_descriptions_from_config(capsys, packages):
    """
    Test that rpmlint updates 'parametrized' descriptions from configuration.

    We test that "parametrized" errors (non-standard-dir-in-usr
    and non-standard-dir-in-var) were overridden by values from
    'descriptions.config' file.
    """
    additional_options = {
        'config': [get_tested_path('configs/descriptions.config')],
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


@pytest.mark.skipif(not HAS_RPMDB, reason='No RPM database present')
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


@pytest.mark.skipif(not HAS_RPMDB, reason='No RPM database present')
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


@pytest.mark.skipif(not HAS_RPMDB, reason='No RPM database present')
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


@pytest.mark.skipif(not HAS_RPMDB, reason='No RPM database present')
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


@pytest.mark.skipif(not HAS_CHECKBASHISMS, reason='Optional dependency checkbashisms not installed')
@pytest.mark.skipif(not HAS_DASH, reason='Optional dependency dash not installed')
@pytest.mark.parametrize('packages', [list(Path('test').glob('*/*.rpm'))])
@pytest.mark.parametrize('configs', [list(Path('configs').glob('*/*.toml'))])
@pytest.mark.no_cover
def test_run_full_rpm(capsys, packages, configs):
    # the package cannot be extracted using rpm2cpio because it contains a directory without 'x' permission
    packages.remove(Path('test/binary/python311-pytest-xprocess-0.23.0-2.4.noarch.rpm'))

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


@pytest.mark.skipif(not HAS_CHECKBASHISMS, reason='Optional dependency checkbashisms not installed')
@pytest.mark.skipif(not HAS_DASH, reason='Optional dependency dash not installed')
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


@pytest.mark.skipif(not HAS_CHECKBASHISMS, reason='Optional dependency checkbashisms not installed')
@pytest.mark.skipif(not HAS_DASH, reason='Optional dependency dash not installed')
@pytest.mark.parametrize('packages', [Path('test/spec')])
@pytest.mark.no_cover
def test_run_full_directory(capsys, packages):
    assert packages.is_dir()
    file_list = [item for item in packages.iterdir() if item.is_file()]
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


@pytest.mark.skipif(not HAS_CHECKBASHISMS, reason='Optional dependency checkbashisms not installed')
@pytest.mark.skipif(not HAS_DASH, reason='Optional dependency dash not installed')
def test_run_empty(capsys):
    linter = Lint(options_preset)
    linter.run()
    out, err = capsys.readouterr()
    assert err
    assert '0 packages and 0 specfiles checked; 0 errors, 0 warnings' in out


@pytest.mark.skipif(not HAS_CHECKBASHISMS, reason='Optional dependency checkbashisms not installed')
@pytest.mark.skipif(not HAS_DASH, reason='Optional dependency dash not installed')
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


@pytest.mark.skipif(not HAS_CHECKBASHISMS, reason='Optional dependency checkbashisms not installed')
@pytest.mark.skipif(not HAS_DASH, reason='Optional dependency dash not installed')
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


@pytest.mark.skipif(not HAS_CHECKBASHISMS, reason='Optional dependency checkbashisms not installed')
@pytest.mark.skipif(not HAS_DASH, reason='Optional dependency dash not installed')
@pytest.mark.parametrize('packages', [Path('test/rpmlintrc/single/sample.spec')])
def test_run_rpmlintrc_single_file(capsys, packages):
    additional_options = {
        'rpmfile': [packages],
        'rpmlintrc': [TEST_RPMLINTRC]
    }
    options = {**options_preset, **additional_options}
    linter = Lint(options)
    linter.run()
    out, err = capsys.readouterr()
    assert not err
    assert 'rpmlintrc:' in out
    assert 'E: unused-rpmlintrc-filter "I am not used"' in out
    assert 'E: unused-rpmlintrc-filter "She is not used"' not in out
    assert 'no-%build-section' not in out


@pytest.mark.skipif(not HAS_RPMDB, reason='No RPM database present')
def test_installed_package(capsys):
    additional_options = {
        'installed': ['bzip2'],
        'permissive': True
    }
    options = {**options_preset, **additional_options}
    linter = Lint(options)
    retcode = linter.run()
    out, err = capsys.readouterr()
    assert '1 packages and 0 specfiles checked' in out
    assert retcode == 0


def _lint_stdout(paths, jobs, capsys):
    additional_options = {
        'rpmfile': [Path(p) for p in paths],
        'jobs': jobs,
    }
    options = {**options_preset, **additional_options}
    linter = Lint(options)
    linter.run()
    out, _ = capsys.readouterr()
    return out


def test_parallel_output_matches_sequential(capsys):
    """
    Worker processes must not tangle the output: parallel runs have to
    produce the same results in the same order as the sequential run.
    """
    import re
    paths = [
        'test/binary/alternatives-ok-1.0-0.x86_64.rpm',
        'test/binary/bcc-lua-0.10.0-86.12.x86_64.rpm',
        'test/spec/SpecCheck2.spec',
    ]
    out_seq = _lint_stdout(paths, 1, capsys)
    out_par = _lint_stdout(paths, 2, capsys)

    # durations and temporary extraction paths vary between runs
    def normalize(s):
        s = re.sub(r'has taken [\d.]+ s', 'has taken X s', s)
        return re.sub(r'/tmp/rpmlint\.[^/:\s]+/', '/tmp/rpmlint.XXX/', s)
    assert normalize(out_seq) == normalize(out_par)
