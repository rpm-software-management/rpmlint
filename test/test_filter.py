from pathlib import Path

from rpmlint.config import Config
from rpmlint.filter import Filter

from Testing import get_tested_package, testpath

TEST_CONFIG_FILTERS = [testpath() / 'configs/testfilters.config']
TEST_RPMLINTRC = testpath() / 'configs/testing-rpmlintrc'
TEST3_RPMLINTRC = testpath() / 'configs/testing3-rpmlintrc'
TEST_PACKAGE = Path('binary', 'ngircd')
TEST_PACKAGE2 = Path('binary', 'tempfiled')
TEST_DESCRIPTIONS = [testpath() / 'configs/descriptions.config']


def test_filters_regexp():
    """
    Load some filters and make sure we generate nice regexp
    """
    cfg = Config(TEST_CONFIG_FILTERS)
    assert len(cfg.configuration['Filters']) == 12
    assert cfg.configuration['Filters'][0] == '.*invalid-buildhost.*'


def test_data_storing(tmpdir):
    """
    Load some filters and make sure we generate nice regexp
    """
    cfg = Config(TEST_CONFIG_FILTERS)
    cfg.load_rpmlintrc(TEST_RPMLINTRC)
    result = Filter(cfg)
    pkg = get_tested_package(TEST_PACKAGE, tmpdir)
    # this should be upgraded to error
    result.add_info('I', pkg, 'suse-other-error', '')
    assert len(result.results) == 1
    assert result.printed_messages['I'] == 0
    assert result.printed_messages['E'] == 1
    # this should be downgraded
    result.add_info('E', pkg, 'dbus-file-unauthorized', '')
    assert len(result.results) == 2
    assert result.printed_messages['W'] == 1
    assert result.printed_messages['E'] == 1


def test_data_storing_backward_compat(tmpdir):
    """
    Make sure we can load some filters from rpmlintrc that
    worked with rpmlint v1.
    """
    cfg = Config(TEST_CONFIG_FILTERS)
    cfg.load_rpmlintrc(TEST3_RPMLINTRC)
    parsed_filters = cfg.rpmlintrc_filters
    assert 'no-spaces-in-paren' in parsed_filters
    assert 'has-spaces-in-paren' in parsed_filters
    assert 'multiple-spaces-in-paren' in parsed_filters
    assert 'doublequotes-instead-of-singlequotes' in parsed_filters


def test_description_storing(tmpdir):
    """
    Test if we can store extra destcriptions and formatting is up par
    """
    lorem_formated = """Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor
incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis
nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat.
Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore
eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt
in culpa qui officia deserunt mollit anim id est laborum.\n\n"""
    cfg = Config(TEST_CONFIG_FILTERS)
    result = Filter(cfg)
    pkg = get_tested_package(TEST_PACKAGE, tmpdir)
    assert len(result.results) == 0
    result.add_info('E', pkg, 'dbus-file-unauthorized', '')
    # two options so we check the description is added only once
    result.add_info('I', pkg, 'suse-other-error', '/usr/bin/1')
    # nothing is populated
    assert not result.get_description('suse-other-error')
    # add descriptions
    result.error_details.update({'suse-other-error': 'Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.'})
    assert result.get_description('suse-other-error') == lorem_formated


def test_description_from_toml(tmpdir):
    """
    Test if description loaded from toml shows up details
    """
    cfg = Config(TEST_CONFIG_FILTERS)
    result = Filter(cfg)
    assert result.get_description('uncompressed-zip')
    assert result.get_description('uncompressed-zip') == 'The zip file is not compressed.\n\n'


def test_description_from_conf(tmpdir):
    """
    Test that descriptions strings are updated from configuration file.

    Load [Descriptions] from TEST_DESCRIPTIONS config file and test that the
    rpmlint error details are updated to the new values.
    """
    cfg = Config(TEST_DESCRIPTIONS)
    result = Filter(cfg)

    assert result.get_description('no-binary', cfg)
    assert result.get_description('no-binary', cfg) == \
        'A new text for no-binary error.\n\n'

    assert result.get_description('no-soname', cfg)
    assert result.get_description('no-soname', cfg) == \
        'A new text for no-soname error.\n\n'

    # At this point, only basic descriptions from "descriptions" directory are
    # loaded. "Dynamic" descriptions that are defined directly in the check
    # file (e.g. see FHSCheck.py and its fhs_details_dict) are loaded later so
    # we can't test it now. It's tested in test_lint.py.

    assert not result.get_description('non-standard-dir-in-usr', cfg)
    assert result.get_description('non-standard-dir-in-usr', cfg) != \
        'A new text for non-standard-dir-in-usr error.\n\n'

    assert not result.get_description('non-standard-dir-in-var', cfg)
    assert result.get_description('non-standard-dir-in-var', cfg) != \
        'A new text for non-standard-dir-in-var error.\n\n'


def test_output(tmpdir):
    """
    Test the actual output of rpmlint on one file
    """
    expected_output = """ngircd.x86_64: I: suse-other-error /usr/bin/1
ngircd.x86_64: I: suse-other-error /usr/bin/2
tempfiled.x86_64: E: suse-other-error /usr/bin/3
Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor
incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis
nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat.
Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore
eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt
in culpa qui officia deserunt mollit anim id est laborum.

ngircd.x86_64: E: dbus-file-unauthorized
Packaging D-Bus services requires a review and whitelisting by the SUSE
security team. If the package is intended for inclusion in any SUSE product
please open a bug report to request review of the package by the security
team. Please refer to
https://en.opensuse.org/openSUSE:Package_security_guidelines#audit_bugs for
more information.\n\n"""
    cfg = Config(TEST_CONFIG_FILTERS)
    result = Filter(cfg)
    pkg = get_tested_package(TEST_PACKAGE, tmpdir)
    pkg2 = get_tested_package(TEST_PACKAGE2, tmpdir)
    # here we check if empty detail will not add whitespace
    result.add_info('E', pkg, 'dbus-file-unauthorized', '')
    # two options so we check the description is added only once
    result.add_info('I', pkg, 'suse-other-error', '/usr/bin/1')
    result.add_info('I', pkg, 'suse-other-error', '/usr/bin/2')
    result.add_info('E', pkg2, 'suse-other-error', '/usr/bin/3')
    result.error_details.update({'suse-other-error': 'Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.'})
    assert len(result.print_results(result.results).splitlines()) == 4
    result.info = True
    assert len(result.print_results(result.results).splitlines()) == 18
    assert result.print_results(result.results) == expected_output


def test_filtered_output(tmpdir):
    cfg = Config(TEST_CONFIG_FILTERS)
    result = Filter(cfg)
    pkg = get_tested_package(TEST_PACKAGE, tmpdir)
    assert len(result.results) == 0
    result.add_info('E', pkg, 'no-regex', '')
    result.add_info('E', pkg, 'no-regex-with-leading-space', '')
    result.add_info('E', pkg, 'bad-error', 'details of the error')
    result.add_info('E', pkg, 'test-color-error', 'details of the error')
    assert len(result.results) == 0


def test_blocked_filters(tmpdir):
    key = 'fatal-error'
    cfg = Config(TEST_CONFIG_FILTERS)
    result = Filter(cfg)
    pkg = get_tested_package(TEST_PACKAGE, tmpdir)
    assert len(result.results) == 0
    assert key in cfg.configuration['Filters']
    result.add_info('E', pkg, key, '')
    assert len(result.results) == 1
