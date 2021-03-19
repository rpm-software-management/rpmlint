import pytest
from rpmlint.checks.TagsCheck import TagsCheck
from rpmlint.filter import Filter

from Testing import CONFIG, get_tested_package


@pytest.fixture(scope='function', autouse=True)
def tagscheck():
    CONFIG.info = True
    output = Filter(CONFIG)
    test = TagsCheck(CONFIG, output)
    return output, test


@pytest.mark.parametrize('package', ['binary/unexpanded1'])
def test_unexpanded_macros(tmpdir, package, tagscheck):
    output, test = tagscheck
    test.check(get_tested_package(package, tmpdir))
    out = output.print_results(output.results)
    assert 'unexpanded-macro Recommends' in out
    assert 'unexpanded-macro Provides' in out
    assert 'unexpanded-macro Conflicts' in out
    assert 'unexpanded-macro Suggests' in out
    assert 'unexpanded-macro Obsoletes' in out
    assert 'unexpanded-macro Enhances' in out


@pytest.mark.parametrize('package', ['binary/self'])
def test_self_provides(tmpdir, package, tagscheck):
    output, test = tagscheck
    test.check(get_tested_package(package, tmpdir))
    out = output.print_results(output.results)
    assert 'E: useless-provides self' in out


@pytest.mark.parametrize('package', ['binary/foo-devel'])
def test_development_package(tmpdir, package, tagscheck):
    output, test = tagscheck
    test.check(get_tested_package(package, tmpdir))
    out = output.print_results(output.results)
    assert 'W: devel-package-with-non-devel-group Games' in out


@pytest.mark.parametrize('package', ['binary/missingprovides'])
def test_missing_provides(tmpdir, package, tagscheck):
    output, test = tagscheck
    test.check(get_tested_package(package, tmpdir))
    out = output.print_results(output.results)
    assert 'E: no-pkg-config-provides' in out


@pytest.mark.parametrize('package', ['binary/invalid-exception'])
def test_invalid_license_exception(tmpdir, package, tagscheck):
    output, test = tagscheck
    test.check(get_tested_package(package, tmpdir))
    out = output.print_results(output.results)
    assert 'W: invalid-license-exception sparta' in out


@pytest.mark.parametrize('package', ['binary/valid-exception'])
def test_valid_license_exception(tmpdir, package, tagscheck):
    CONFIG.info = True
    CONFIG.configuration['ValidLicenseExceptions'] = ['389-exception']
    output = Filter(CONFIG)
    test = TagsCheck(CONFIG, output)
    test.check(get_tested_package(package, tmpdir))
    out = output.print_results(output.results)
    assert 'W: invalid-license-exception' not in out


@pytest.mark.parametrize('package', ['binary/xtables-addons-kmp-default'])
def test_forbidden_controlchar_found_requires(tmpdir, package, tagscheck):
    output, test = tagscheck
    test.check(get_tested_package(package, tmpdir))
    out = output.print_results(output.results)
    assert 'E: forbidden-controlchar-found Requires:' in out


@pytest.mark.parametrize('package', ['binary/ruby2.6-rubygem-fast_gettext'])
def test_forbidden_controlchar_found_changelog(tmpdir, package, tagscheck):
    output, test = tagscheck
    test.check(get_tested_package(package, tmpdir))
    out = output.print_results(output.results)
    assert 'E: forbidden-controlchar-found %changelog' in out


@pytest.mark.parametrize('package', ['binary/SpecCheck4'])
def test_forbidden_controlchar_found(tmpdir, package, tagscheck):
    output, test = tagscheck
    test.check(get_tested_package(package, tmpdir))
    out = output.print_results(output.results)
    assert 'E: forbidden-controlchar-found Requires:' in out
    assert 'E: forbidden-controlchar-found Provides:' in out
    assert 'E: forbidden-controlchar-found Obsoletes:' in out
    assert 'E: forbidden-controlchar-found Conflicts:' in out
    assert 'E: forbidden-controlchar-found %changelog :' in out


@pytest.mark.parametrize('package', ['binary/shlib2-devel'])
def test_shlib2_devel(tmpdir, package, tagscheck):
    output, test = tagscheck
    test.check(get_tested_package(package, tmpdir))
    out = output.print_results(output.results)
    assert 'W: no-dependency-on' in out


@pytest.mark.parametrize('package', ['binary/unexpanded-macro-exp'])
def test_check_unexpanded_macro(tmpdir, package, tagscheck):
    """Test if a package has an unexpanded macro in it's specfile."""
    output, test = tagscheck
    test.check(get_tested_package(package, tmpdir))
    out = output.print_results(output.results)
    assert 'W: unexpanded-macro Packager %ppc' in out
    assert 'W: unexpanded-macro Group %ppc' in out
    assert 'W: unexpanded-macro Provides /something%ppc %ppc' in out
    assert 'W: unexpanded-macro Conflicts something:%ppc %ppc' in out
    assert 'W: unexpanded-macro Supplements packageand(python-gobject:%{gdk_real_package})%ppc %ppc' in out
    assert 'W: unexpanded-macro Suggests /%ppc %ppc' in out
    assert 'W: unexpanded-macro Enhances /%ppc %ppc' in out
    assert 'W: unexpanded-macro Recommends /%ppc %ppc' in out
    assert 'W: unexpanded-macro Supplements packageand(python-gobject:%{gdk_real_package})%ppc %{gdk_real_package}' in out
    assert 'W: unexpanded-macro Supplements packageand(python-gobject:%{gdk_real_package})%ppc %ppc' in out


@pytest.mark.parametrize('package', ['binary/invalid-version'])
def test_check_errors(tmpdir, package, tagscheck):
    """Test package for check invalid-version."""
    output, test = tagscheck
    test.check(get_tested_package(package, tmpdir))
    out = output.print_results(output.results)
    # Test if a package has a Version: tag with pre/alpha/beta suffixes in it's specfile
    assert 'E: invalid-version 0pre' in out


# TODO: Add a test for no-changelogname-tag not in out


@pytest.mark.parametrize('package', ['binary/summary-warning'])
def test_check_summary_warning(tmpdir, package, tagscheck):
    """Test package for check
    - in out,
        summary-too-long, summary-has-leading-spaces,
        description-shorter-than-summary,
    - not in out
    invalid-version, unexpanded-macro.
    """
    output, test = tagscheck
    test.check(get_tested_package(package, tmpdir))
    out = output.print_results(output.results)
    # Test if package has a summary longer than 80 characters
    assert 'E: summary-too-long   lorem Ipsum is simply dummy text of the printing and typesetting industry' in out
    # Test if package has leading space at the beginning of the summary
    assert 'E: summary-has-leading-spaces   lorem Ipsum is simply dummy text of the printing and typesetting industry' in out
    # Test if package has a shorter description than Summary
    assert 'W: description-shorter-than-summary' in out
    # Test if a package has a Version: tag
    # without any pre/alpha/beta suffixes in it's specfile.
    assert 'E: invalid-version' not in out
    # Test if a package does not have an unexpanded
    # macro in it's specfile.
    assert 'W: unexpanded-macro' not in out
    assert 'E: no-group-tag' in out


@pytest.mark.parametrize('package', ['binary/no-url-tag'])
def test_check_warning(tmpdir, package, tagscheck):
    """Test if a package contains the warning for
    summary-not-capitalized, summary-ended-with-dot,
    no-url-tag."""
    output, test = tagscheck
    test.check(get_tested_package(package, tmpdir))
    out = output.print_results(output.results)
    # Test if package Summary does not start with a capital letter
    assert 'W: summary-not-capitalized no-url-tag warning.' in out
    # Test if a package Summary ends with a period
    assert 'W: summary-ended-with-dot no-url-tag warning.' in out
    # Test if a package does not contain a Url: tag
    assert 'W: no-url-tag' in out


@pytest.mark.parametrize('package', ['binary/invalid-la-file'])
def test_check_errors_not_found(tmpdir, package, tagscheck):
    """Test packages for checks
    summary-too-long, summary-not-capitalized,
    summary-ended-with-dot, summary-has-leading-spaces,
    no-url-tag, description-shorter-than-summary.
    """
    output, test = tagscheck
    test.check(get_tested_package(package, tmpdir))
    out = output.print_results(output.results)
    # Test if a package Summary is not longer than 80 characters
    assert 'W: summary-too-long' not in out
    # Test if Summary starts with a capitalized word
    assert 'W: summary-not-capitalized' not in out
    # Test if a package Summary does not end with a period
    assert 'W: summary-ended-with-dot' not in out
    # Test if a package Summary does not begin with a leading space
    assert 'W: summary-has-leading-spaces' not in out
    # Test if a package contains a Url: tag
    assert 'W: no-url-tag' not in out
    # Test if package no shorter description than Summary
    assert 'W: description-shorter-than-summary' not in out


@pytest.mark.parametrize('package', ['binary/misc-warnings'])
def test_check_misc_warning(tmpdir, package, tagscheck):
    """Test package for check tag-in-description,
    name-repeated-in-summary, invalid-url."""
    output, test = tagscheck
    test.check(get_tested_package(package, tmpdir))
    out = output.print_results(output.results)
    # Test if a package has a tag such as Name: in the description
    assert 'W: tag-in-description Name:' in out
    # Test if a package has it's name repeated in the summary tag
    assert 'W: name-repeated-in-summary misc-warnings' in out
    # Test if a package has a invalid url value in the URL: tag
    assert 'W: invalid-url URL so;mething.' in out


@pytest.mark.parametrize('package', ['binary/misc-no-warnings'])
def test_check_misc_warning_not_found(tmpdir, package, tagscheck):
    """Test package for check not in out
    tag-in-description, name-repeated-in-summary, invalid-url."""
    output, test = tagscheck
    test.check(get_tested_package(package, tmpdir))
    out = output.print_results(output.results)
    # Test if a package does not have a tag in description
    assert 'W: tag-in-description' not in out
    # Test if a package does not have a name repeated in the summary tag value
    assert 'W: name-repeated-in-summary' not in out
    # Test if a package does not have a invalid url in the URL tag value
    assert 'W: invalid-url' not in out


@pytest.mark.parametrize('package', ['binary/invalid-dependency'])
def test_check_invalid_dependency(tmpdir, package, tagscheck):
    """Test if a package has
    invalid-dependency, no-description-tag, unreasonable-epoch."""
    output, test = tagscheck
    test.check(get_tested_package(package, tmpdir))
    out = output.print_results(output.results)
    # Test if a package has a Epoch tag value greater than 99
    assert 'W: unreasonable-epoch 100' in out
    # Test if a package has Requires: starts with /usr/local
    assert 'E: invalid-dependency /usr/local/something' in out
    # Test if a package has empty or no description tag
    assert 'E: no-description-tag' in out


@pytest.mark.parametrize('package', ['binary/random-exp'])
def test_package_random_warnings(tmpdir, package, tagscheck):
    """Test if a package has check,
    - in out,
        obsolete-not-provided
        description-line-too-long,
    - not in out,
        invalid-dependency,
        unreasonable-epoch,
        no-description-tag,
        self-obsoletion."""
    output, test = tagscheck
    test.check(get_tested_package(package, tmpdir))
    out = output.print_results(output.results)
    # Test if a package that was obsoleted is still provided
    # in newer package to avoid unnecessary dependency breakage
    assert 'W: obsolete-not-provided' in out
    # Test if a package has a description longer than 79 characters
    assert 'E: description-line-too-long This is ridiculously long description that has no meaning but is used to test the check description-line-too-long.' in out
    # Test if a package has a Requires tag value start with
    # string other than /usr/local/
    assert 'E: invalid-dependency' not in out
    # Test if a package has a Epoch tag value less than or equal to 99
    assert 'W: unreasonable-epoch' not in out
    # Test if a package has a non-empty description tag
    assert 'W: no-description-tag' not in out
    # Test if a package does not have itself in Obsoletes: tag value
    assert 'W: self-obsoletion' not in out


@pytest.mark.parametrize('package', ['binary/random-devel'])
def test_package_random_exp(tmpdir, package, tagscheck):
    """Test if a package check,
    - in out,
        self-obsoletion,
    - not in out,
        obsolete-not-provided,
        description-line-too-long,
        devel-dependency."""
    output, test = tagscheck
    test.check(get_tested_package(package, tmpdir))
    out = output.print_results(output.results)
    # Test if a package obsoletes itself i.e. Obsoletes: random-devel
    assert 'W: self-obsoletion random-devel obsoletes random-devel' in out
    # Test if a obsoleted package has been provided to
    # to avoid unnecessary breakage i.e. Requires: python
    assert 'W: obsolete-not-provided' not in out
    # Test if a package has a description line not greater 79 characters
    assert 'E: description-line-too-long' not in out
    # Test if a package is a *-devel package and requires a devel dependency
    assert 'W: devel-dependency' not in out


@pytest.mark.parametrize('package', ['binary/requires-on-release'])
def test_check_requires_on_release(tmpdir, package, tagscheck):
    """Test if a package check,
    - in out,
        requires-on-release."""
    output, test = tagscheck
    test.check(get_tested_package(package, tmpdir))
    out = output.print_results(output.results)
    # Test if a package requires specific release of another package
    assert 'W: requires-on-release baz = 2.1-1' in out


@pytest.mark.parametrize('package', ['binary/invalid-license'])
def test_check_invalid_license(tmpdir, package, tagscheck):
    """Test if a package check,
    - in out,
        invalid-license,
    - not in out,
        requires-on-release."""
    CONFIG.configuration['ValidLicenses'] = ['MIT']
    output = Filter(CONFIG)
    test = TagsCheck(CONFIG, output)
    test.check(get_tested_package(package, tmpdir))
    out = output.print_results(output.results)
    # Test if a package has a License: tag value different from
    # ValidLicense = [] list in configuration
    assert 'W: invalid-license Apache License' in out
    # Test if a package does not Requires: a specific version of a package
    assert 'W: requires-on-release' not in out


@pytest.mark.parametrize('package', ['binary/not-standard-release-extension'])
def test_package_not_std_release_extension(tmpdir, package, tagscheck):
    """Test if package has check,
    - in out,
        not-standard-release-extension
    - not in out,
        invalid-license."""
    CONFIG.configuration['ReleaseExtension'] = 'hello$'
    CONFIG.configuration['ValidLicenses'] = ['Apache-2.0 License']
    output = Filter(CONFIG)
    test = TagsCheck(CONFIG, output)
    test.check(get_tested_package(package, tmpdir))
    out = output.print_results(output.results)
    # Test if a package has a ReleaseExtension regex does not match with the Release: tag value expression
    # i.e. Release tag value must not match regex expression 'hello$'
    assert 'W: not-standard-release-extension 1.1' in out
    # Test if a package does have the same License value as defined in the ValidLicense in configdefaults
    assert 'W: invalid-license Apache-2.0 License' not in out


@pytest.mark.parametrize('package', ['binary/non-standard-group'])
def test_check_non_standard_group(tmpdir, package, tagscheck):
    """Test if a package has check,
    - in out,
        non-standard-group
    - not in out,
        not-standard-release-extension."""
    CONFIG.configuration['ValidGroups'] = ['Devel/Something']
    CONFIG.configuration['ReleaseExtension'] = '0'
    output = Filter(CONFIG)
    test = TagsCheck(CONFIG, output)
    test.check(get_tested_package(package, tmpdir))
    out = output.print_results(output.results)
    # Test if a package has a different Group: tag value than ValidGroups = []
    assert 'W: non-standard-group non/standard/group' in out
    # Test if a package matches the Release tag regex
    assert 'not-standard-release-extension 0' not in out


@pytest.mark.parametrize('package', ['binary/dev-dependency'])
def test_package_dev_dependency(tmpdir, package, tagscheck):
    """Test if a package check,
    - in out,
        devel-dependency,
    - not in out,
        non-standard-group."""
    CONFIG.configuration['ValidGroups'] = ['Devel/Something']
    output = Filter(CONFIG)
    test = TagsCheck(CONFIG, output)
    test.check(get_tested_package(package, tmpdir))
    out = output.print_results(output.results)
    # Test if a package is not a devel package itself but requires a devel dependency
    assert 'E: devel-dependency glibc-devel' in out
    # Test if a package does not have a Group tag
    assert 'W: non-standard-group Devel/Something' not in out


@pytest.mark.parametrize('package', ['binary/summary-on-multiple-lines'])
def test_summary_on_multiple_lines(tmpdir, package, tagscheck):
    # Test if a package has summary on multiple lines.
    output, test = tagscheck
    test.check(get_tested_package(package, tmpdir))
    out = output.print_results(output.results)
    assert 'E: summary-on-multiple-lines' in out
