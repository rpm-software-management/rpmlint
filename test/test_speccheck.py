import re

import pytest
from rpmlint.checks.SpecCheck import SpecCheck
from rpmlint.filter import Filter

from Testing import CONFIG, get_tested_package, get_tested_spec_package


@pytest.fixture(scope='function', autouse=True)
def speccheck():
    CONFIG.info = True
    output = Filter(CONFIG)
    test = SpecCheck(CONFIG, output)
    return output, test


def test_check_include(tmpdir, speccheck):
    output, test = speccheck
    test.check_source(get_tested_package('source/CheckInclude', tmpdir))
    out = output.print_results(output.results)
    assert "specfile-error can't parse specfile" not in out
    assert 'no-buildroot-tag' in out
    assert 'E: specfile-error error: query of specfile' not in out


@pytest.mark.parametrize('package', ['spec/SpecCheck2', 'spec/SpecCheck3'])
def test_patch_not_applied(package, speccheck):
    output, test = speccheck
    pkg = get_tested_spec_package(package)
    test.check_spec(pkg)
    out = output.print_results(output.results)
    assert 'patch-not-applied' not in out


@pytest.mark.parametrize('package', ['spec/SpecCheck'])
def test_distribution_tags(package, speccheck):
    output, test = speccheck
    pkg = get_tested_spec_package(package)
    test.check_spec(pkg)
    out = output.print_results(output.results)
    assert 'patch-not-applied Patch3' in out
    assert not re.search(r'patch-not-applied Patch\b', out)
    assert not re.search('patch-not-applied Patch[0124567]', out)
    assert 'libdir-macro-in-noarch-package' not in out
    assert len(re.findall('macro-in-comment', out)) == 1
    assert 'unversioned-explicit-provides unversioned-provides' in out
    assert 'unversioned-explicit-provides versioned-provides' not in out
    assert 'unversioned-explicit-provides /' not in out
    assert 'unversioned-explicit-obsoletes unversioned-obsoletes' in out
    assert 'unversioned-explicit-obsoletes versioned-obsoletes' not in out
    assert 'unversioned-explicit-obsoletes /' not in out
    assert 'setup-not-quiet' in out


@pytest.mark.parametrize('package', ['spec/SpecCheck4'])
def test_forbidden_controlchars_found(package, speccheck):
    output, test = speccheck
    pkg = get_tested_spec_package(package)
    test.check_spec(pkg)
    out = output.print_results(output.results)
    assert 'E: forbidden-controlchar-found Requires:' in out
    assert 'E: forbidden-controlchar-found Provides:' in out
    assert 'E: forbidden-controlchar-found Obsoletes:' in out
    assert 'E: forbidden-controlchar-found Conflicts:' in out
    assert 'E: forbidden-controlchar-found %changelog:' in out


@pytest.mark.parametrize('package', ['source/no-spec-file'])
def test_check_no_spec_file(tmpdir, package, speccheck):
    """Test if spec file is not found inside RPM metadata."""
    output, test = speccheck
    test.check(get_tested_package(package, tmpdir))
    out = output.print_results(output.results)
    assert 'E: no-spec-file' in out


@pytest.mark.parametrize('package', ['source/CheckInclude'])
def test_check_no_spec_file_not_applied(tmpdir, package, speccheck):
    """Test if there is no spec file inside RPM metadata."""
    output, test = speccheck
    test.check(get_tested_package(package, tmpdir))
    out = output.print_results(output.results)
    assert 'E: no-spec-file' not in out


@pytest.mark.parametrize('package', ['spec/non-utf8-spec-file'])
def test_check_non_utf8_spec_file(package, speccheck):
    """Test if specfile does not have UTF-8 character encoding."""
    output, test = speccheck
    pkg = get_tested_spec_package(package)
    test.check_spec(pkg)
    out = output.print_results(output.results)
    assert 'E: non-utf8-spec-file' in out


@pytest.mark.parametrize('package', ['spec/SpecCheckTemp'])
def test_check_non_utf8_spec_file_not_applied(package, speccheck):
    """Test if specfile has UTF-8 character encoding."""
    output, test = speccheck
    pkg = get_tested_spec_package(package)
    test.check_spec(pkg)
    out = output.print_results(output.results)
    assert 'E: non-utf8-spec-file' not in out


@pytest.mark.parametrize('package', ['source/invalid-spec-name'])
def test_check_invalid_spec_name(tmpdir, package, speccheck):
    """Test if specfile name does not matches the ('Name: ') tag."""
    output, test = speccheck
    test.check(get_tested_package(package, tmpdir))
    out = output.print_results(output.results)
    assert 'E: invalid-spec-name' in out


@pytest.mark.parametrize('package', ['source/CheckInclude'])
def test_check_invalid_spec_name_not_applied(tmpdir, package, speccheck):
    """Test if specfile has specfile name as ('Name: ') tag."""
    output, test = speccheck
    test.check(get_tested_package(package, tmpdir))
    out = output.print_results(output.results)
    assert 'E: invalid-spec-name' not in out


@pytest.mark.parametrize('package', ['spec/non-break-space'])
def test_check_non_break_space(package, speccheck):
    """Test if specfile has a nbsp character."""
    output, test = speccheck
    pkg = get_tested_spec_package(package)
    test.check_spec(pkg)
    out = output.print_results(output.results)
    assert 'W: non-break-space' in out


@pytest.mark.parametrize('package', ['spec/SpecCheck2'])
def test_check_non_break_space_not_applied(package, speccheck):
    """Test if specfile does not have any nbsp character."""
    output, test = speccheck
    pkg = get_tested_spec_package(package)
    test.check_spec(pkg)
    out = output.print_results(output.results)
    assert 'W: non-break-space' not in out


@pytest.mark.parametrize('package', ['spec/rpm-buildroot-usage'])
def test_check_rpm_buildroot_usage_under_prep(package, speccheck):
    """Test if specfile has buildroot macro under %prep."""
    output, test = speccheck
    pkg = get_tested_spec_package(package)
    test.check_spec(pkg)
    out = output.print_results(output.results)
    assert 'E: rpm-buildroot-usage' in out


@pytest.mark.parametrize('package', ['spec/SpecCheckTemp'])
def test_check_rpm_buildroot_usage_under_build(package, speccheck):
    """Test if specfile has buildroot macro under %build."""
    output, test = speccheck
    pkg = get_tested_spec_package(package)
    test.check_spec(pkg)
    out = output.print_results(output.results)
    assert 'E: rpm-buildroot-usage' in out


@pytest.mark.parametrize('package', ['spec/SpecCheck2'])
def test_check_rpm_buildroot_usage_not_applied(package, speccheck):
    """Test if specfile does not have buildroot macro inside specfile."""
    output, test = speccheck
    pkg = get_tested_spec_package(package)
    test.check_spec(pkg)
    out = output.print_results(output.results)
    assert 'E: rpm-buildroot-usage' not in out


@pytest.mark.parametrize('package', ['spec/make-check-outside-check-section'])
def test_check_make_check_outside_check_section(package, speccheck):
    """Test if specfile has `make check` outside %check."""
    output, test = speccheck
    pkg = get_tested_spec_package(package)
    test.check_spec(pkg)
    out = output.print_results(output.results)
    assert 'W: make-check-outside-check-section' in out


@pytest.mark.parametrize('package', ['spec/SpecCheckTemp'])
def test_check_make_check_inside_check_section(package, speccheck):
    """Test if specfile has `make check` inside all the required
    ('check', 'changelog', 'package', 'description') section.
    """
    output, test = speccheck
    pkg = get_tested_spec_package(package)
    test.check_spec(pkg)
    out = output.print_results(output.results)
    assert 'W: make-check-outside-check-section' not in out


@pytest.mark.parametrize('package', ['spec/SpecCheck2'])
def test_check_make_check_outside_not_applied(package, speccheck):
    """Test if specfile does not have any `make check`."""
    output, test = speccheck
    pkg = get_tested_spec_package(package)
    test.check_spec(pkg)
    out = output.print_results(output.results)
    assert 'W: make-check-outside-check-section' not in out


@pytest.mark.parametrize('package', ['spec/setup-not-quiet'])
def test_check_setup_not_quiet(package, speccheck):
    """Test if specfile does not have %setup -q macro."""
    output, test = speccheck
    pkg = get_tested_spec_package(package)
    test.check_spec(pkg)
    out = output.print_results(output.results)
    assert 'W: setup-not-quiet' in out


@pytest.mark.parametrize('package', ['spec/SpecCheckTemp'])
def test_check_setup_is_quiet(package, speccheck):
    """Test if specfile has a %setup -q macro."""
    output, test = speccheck
    pkg = get_tested_spec_package(package)
    test.check_spec(pkg)
    out = output.print_results(output.results)
    assert 'W: setup-not-quiet' not in out


@pytest.mark.parametrize('package', ['spec/SpecCheck2'])
def test_check_setup_not_quiet_not_applied(package, speccheck):
    """Test if specfile does not have a setup macro."""
    output, test = speccheck
    pkg = get_tested_spec_package(package)
    test.check_spec(pkg)
    out = output.print_results(output.results)
    assert 'W: setup-not-quiet' not in out


@pytest.mark.parametrize('package', ['spec/setup-not-in-prep'])
def test_check_setup_not_in_prep(package, speccheck):
    """Test if specfile does not have %setup inside %prep."""
    output, test = speccheck
    pkg = get_tested_spec_package(package)
    test.check_spec(pkg)
    out = output.print_results(output.results)
    assert 'W: setup-not-in-prep' in out


@pytest.mark.parametrize('package', ['spec/SpecCheckTemp'])
def test_check_setup_inside_prep(package, speccheck):
    """Test if specfile has %setup inside %prep."""
    output, test = speccheck
    pkg = get_tested_spec_package(package)
    test.check_spec(pkg)
    out = output.print_results(output.results)
    assert 'W: setup-not-in-prep' not in out


@pytest.mark.parametrize('package', ['spec/SpecCheck2'])
def test_check_setup_not_in_prep_not_applied(package, speccheck):
    """Test if specfile has no %setup."""
    output, test = speccheck
    pkg = get_tested_spec_package(package)
    test.check_spec(pkg)
    out = output.print_results(output.results)
    assert 'W: setup-not-in-prep' not in out


@pytest.mark.parametrize('package', ['spec/%autopatch-not-in-prep'])
def test_check_autopatch_not_in_prep(package, speccheck):
    """Test if specfile does not have %autopatch inside %prep."""
    output, test = speccheck
    pkg = get_tested_spec_package(package)
    test.check_spec(pkg)
    out = output.print_results(output.results)
    assert 'W: %autopatch-not-in-prep' in out


@pytest.mark.parametrize('package', ['spec/SpecCheckTemp'])
def test_check_autopatch_in_prep(package, speccheck):
    """Test if specfile has %autopatch inside %prep."""
    output, test = speccheck
    pkg = get_tested_spec_package(package)
    test.check_spec(pkg)
    out = output.print_results(output.results)
    assert 'W: %autopatch-not-in-prep' not in out


@pytest.mark.parametrize('package', ['spec/SpecCheck2'])
def test_check_autopatch_not_in_prep_not_applied(package, speccheck):
    """Test if specfile has no %autopatch."""
    output, test = speccheck
    pkg = get_tested_spec_package(package)
    test.check_spec(pkg)
    out = output.print_results(output.results)
    assert 'W: %autopatch-not-in-prep' not in out


@pytest.mark.parametrize('package', ['spec/%autosetup-not-in-prep'])
def test_check_autosetup_not_in_prep(package, speccheck):
    """Test if specfile does not have %autosetup inside %prep."""
    output, test = speccheck
    pkg = get_tested_spec_package(package)
    test.check_spec(pkg)
    out = output.print_results(output.results)
    assert 'W: %autosetup-not-in-prep' in out


@pytest.mark.parametrize('package', ['spec/SpecCheckTemp'])
def test_check_autosetup_inside_prep(package, speccheck):
    """Test if specfile has %autosetup in %prep."""
    output, test = speccheck
    pkg = get_tested_spec_package(package)
    test.check_spec(pkg)
    out = output.print_results(output.results)
    assert 'W: %autosetup-not-in-prep' not in out


@pytest.mark.parametrize('package', ['spec/SpecCheck2'])
def test_check_autosetup_not_in_prep_not_applied(package, speccheck):
    """Test if specfile has no %autosetup."""
    output, test = speccheck
    pkg = get_tested_spec_package(package)
    test.check_spec(pkg)
    out = output.print_results(output.results)
    assert 'W: %autosetup-not-in-prep' not in out


@pytest.mark.parametrize('package', ['spec/use-of-RPM-SOURCE-DIR'])
def test_check_use_of_rpm_source_dir(package, speccheck):
    """Test if specfile consist of $RPM_SOURCE_DIR or %{_sourcedir}."""
    output, test = speccheck
    pkg = get_tested_spec_package(package)
    test.check_spec(pkg)
    out = output.print_results(output.results)
    assert 'E: use-of-RPM_SOURCE_DIR' in out


@pytest.mark.parametrize('package', ['spec/SpecCheck2'])
def test_check_use_of_rsd_not_applied(package, speccheck):
    """rsd: RPM_SOURCE_DIR
    Test if specfile does not consist of $RPM_SOURCE_DIR or %{_sourcedir}.
    """
    output, test = speccheck
    pkg = get_tested_spec_package(package)
    test.check_spec(pkg)
    out = output.print_results(output.results)
    assert 'E: use-of-RPM_SOURCE_DIR' not in out


@pytest.mark.parametrize('package', ['spec/configure-without-libdir-spec'])
def test_check_configure_without_libdir_spec(package, speccheck):
    """Test if specfile does not have options augmented with --libdir."""
    output, test = speccheck
    pkg = get_tested_spec_package(package)
    test.check_spec(pkg)
    out = output.print_results(output.results)
    assert 'W: configure-without-libdir-spec' in out


@pytest.mark.parametrize('package', ['spec/SpecCheck2'])
def test_check_cwls_not_applied(package, speccheck):
    """cwls: configure-without-libdir-spec
    Test if specfile has options augmented with --libdir.
    """
    output, test = speccheck
    pkg = get_tested_spec_package(package)
    test.check_spec(pkg)
    out = output.print_results(output.results)
    assert 'W: configure-without-libdir-spec' not in out


@pytest.mark.parametrize('package', ['spec/hardcoded-library-path'])
def test_check_hardcoded_library_path(package, speccheck):
    """Test if specfile has hardcoded library path."""
    output, test = speccheck
    pkg = get_tested_spec_package(package)
    test.check_spec(pkg)
    out = output.print_results(output.results)
    assert 'E: hardcoded-library-path' in out


@pytest.mark.parametrize('package', ['spec/SpecCheck2'])
def test_check_hclp_not_applied(package, speccheck):
    """hclp: hardcoded library path
    Test if specfile does not have hardcoded library path.
    """
    output, test = speccheck
    pkg = get_tested_spec_package(package)
    test.check_spec(pkg)
    out = output.print_results(output.results)
    assert 'E: hardcoded-library-path' not in out


@pytest.mark.parametrize('package', ['spec/obsolete-tag'])
def test_check_obsolete_tag(package, speccheck):
    """Test if specfile has obsolete-tag as Copyright or Serial."""
    output, test = speccheck
    pkg = get_tested_spec_package(package)
    test.check_spec(pkg)
    out = output.print_results(output.results)
    assert 'W: obsolete-tag 2' in out
    assert 'W: obsolete-tag Something' in out


@pytest.mark.parametrize('package', ['spec/SpecCheck2'])
def test_check_obsolete_tag_not_applied(package, speccheck):
    """Test if specfile does not have obsolete-tag as Copyright or Serial."""
    output, test = speccheck
    pkg = get_tested_spec_package(package)
    test.check_spec(pkg)
    out = output.print_results(output.results)
    assert 'W: obsolete-tag' not in out


@pytest.mark.parametrize('package', ['spec/hardcoded-path-in-buildroot-tag'])
def test_check_hardcoded_path_in_buildroot_tag(package, speccheck):
    """Test if specfile has hardoded path in buildroot tag."""
    output, test = speccheck
    pkg = get_tested_spec_package(package)
    test.check_spec(pkg)
    out = output.print_results(output.results)
    assert 'W: hardcoded-path-in-buildroot-tag /usr/bin/bash' in out


@pytest.mark.parametrize('package', ['spec/SpecCheck2'])
def test_check_hpbt_not_applied(package, speccheck):
    """hpbt: hardcoded-path-in-buildroot-tag
    Test if specfile does not have hardoded path in buildroot tag.
    """
    output, test = speccheck
    pkg = get_tested_spec_package(package)
    test.check_spec(pkg)
    out = output.print_results(output.results)
    assert 'W: hardcoded-path-in-buildroot-tag %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)' not in out


@pytest.mark.parametrize('package', ['spec/buildarch-instead-of-exclusivearch-tag'])
def test_check_buildarch_instead_of_exclusivearch_tag(package, speccheck):
    """Test if specfile has BuildArch has any architecture beside noarch."""
    output, test = speccheck
    pkg = get_tested_spec_package(package)
    test.check_spec(pkg)
    out = output.print_results(output.results)
    assert 'E: buildarch-instead-of-exclusivearch-tag x86_64' in out
    assert 'E: buildarch-instead-of-exclusivearch-tag i586' in out


@pytest.mark.parametrize('package', ['spec/SpecCheck2'])
def test_check_biet_not_applied(package, speccheck):
    """biet: buildarch-instead-of-exclusivearch-tag
    Test if specfile has BuildArch with noarch.
    """
    output, test = speccheck
    pkg = get_tested_spec_package(package)
    test.check_spec(pkg)
    out = output.print_results(output.results)
    assert 'E: buildarch-instead-of-exclusivearch-tag noarch' not in out


@pytest.mark.parametrize('package', ['spec/hardcoded-packager-tag'])
def test_check_hardcoded_packager_tag(package, speccheck):
    """Test if specfile has hardcoded packager tag."""
    output, test = speccheck
    pkg = get_tested_spec_package(package)
    test.check_spec(pkg)
    out = output.print_results(output.results)
    assert 'W: hardcoded-packager-tag Someone' in out


@pytest.mark.parametrize('package', ['spec/SpecCheck2'])
def test_check_hardcoded_packager_tag_not_applied(package, speccheck):
    """Test if specfile does not have hardcoded packager tag."""
    output, test = speccheck
    pkg = get_tested_spec_package(package)
    test.check_spec(pkg)
    out = output.print_results(output.results)
    assert 'W: hardcoded-packager-tag' not in out


@pytest.mark.parametrize('package', ['spec/hardcoded-prefix-tag'])
def test_check_hardcoded_prefix_tag(package, speccheck):
    """Test if specfile has hardcoded prefix tag."""
    output, test = speccheck
    pkg = get_tested_spec_package(package)
    test.check_spec(pkg)
    out = output.print_results(output.results)
    assert 'W: hardcoded-prefix-tag' in out


@pytest.mark.parametrize('package', ['spec/SpecCheck2'])
def test_check_hardcoded_prefix_tag_not_applied(package, speccheck):
    """Test if specfile does not have hardcoded prefix tag."""
    output, test = speccheck
    pkg = get_tested_spec_package(package)
    test.check_spec(pkg)
    out = output.print_results(output.results)
    assert 'W: hardcoded-prefix-tag' not in out


@pytest.mark.parametrize('package', ['spec/prereq_use'])
def test_check_prereq_use(package, speccheck):
    """Test if specfile has tags such as PreReq(pre)
    or PreReq(post).
    """
    output, test = speccheck
    pkg = get_tested_spec_package(package)
    test.check_spec(pkg)
    out = output.print_results(output.results)
    assert 'E: prereq-use none' in out
    assert 'E: prereq-use none_other' in out


@pytest.mark.parametrize('package', ['spec/patch-not-applied'])
def test_check_prereq_use_not_found(package, speccheck):
    """Test if specfile has no PreReq tag value."""
    output, test = speccheck
    pkg = get_tested_spec_package(package)
    test.check_spec(pkg)
    out = output.print_results(output.results)
    assert 'E: prereq-use' not in out


@pytest.mark.parametrize('package', ['spec/mixed-use-of-spaces-and-tabs'])
def test_check_prereq_use_not_applied(package, speccheck):
    """Test if specfile has no PreReq tag value."""
    output, test = speccheck
    pkg = get_tested_spec_package(package)
    test.check_spec(pkg)
    out = output.print_results(output.results)
    assert 'E: prereq-use' not in out


@pytest.mark.parametrize('package', ['spec/buildprereq-use'])
def test_check_buildprereq_use(package, speccheck):
    """Test if specfile has buildprereq tag."""
    output, test = speccheck
    pkg = get_tested_spec_package(package)
    test.check_spec(pkg)
    out = output.print_results(output.results)
    assert 'E: buildprereq-use Something' in out


@pytest.mark.parametrize('package', ['spec/SpecCheck2'])
def test_check_buildprereq_use_not_applied(package, speccheck):
    """Test if specfile does not have buildprereq tag."""
    output, test = speccheck
    pkg = get_tested_spec_package(package)
    test.check_spec(pkg)
    out = output.print_results(output.results)
    assert 'E: buildprereq-use' not in out


@pytest.mark.parametrize('package', ['spec/forbidden-controlchar-found'])
def test_check_forbidden_controlchar_found(package, speccheck):
    """Test if specfile has forbidden controlchar
    in various parts of specfile.
    """
    output, test = speccheck
    pkg = get_tested_spec_package(package)
    test.check_spec(pkg)
    out = output.print_results(output.results)
    assert 'E: forbidden-controlchar-found' in out


@pytest.mark.parametrize('package', ['spec/SpecCheckTemp'])
def test_check_forbidden_controlchar_not_found(package, speccheck):
    """Test if specfile does not have forbidden controlchar
    in various parts of specfile.
    """
    output, test = speccheck
    pkg = get_tested_spec_package(package)
    test.check_spec(pkg)
    out = output.print_results(output.results)
    assert 'E: forbidden-controlchar-found' not in out


@pytest.mark.parametrize('package', ['spec/comparison-operator-in-deptoken'])
def test_check_coid(package, speccheck):
    """coid: comparison-operator-in-deptoken
    Test if specfile has comparison operator(>, =) in deptoken.
    """
    output, test = speccheck
    pkg = get_tested_spec_package(package)
    test.check_spec(pkg)
    out = output.print_results(output.results)
    assert 'W: comparison-operator-in-deptoken something>2.0' in out
    assert 'W: comparison-operator-in-deptoken Something>1.0' in out
    assert 'W: comparison-operator-in-deptoken Something=2.0' in out


@pytest.mark.parametrize('package', ['spec/SpecCheckTemp'])
def test_check_coid_found(package, speccheck):
    """coid: comparison-operator-in-deptoken
    Test if specfile has comparison operator(<, <=) in deptoken.
    """
    output, test = speccheck
    pkg = get_tested_spec_package(package)
    test.check_spec(pkg)
    out = output.print_results(output.results)
    assert 'W: comparison-operator-in-deptoken Someotherthing<1.0' in out
    assert 'W: comparison-operator-in-deptoken Someotherthing<=2.0' in out


@pytest.mark.parametrize('package', ['spec/SpecCheck2'])
def test_check_coid_is_found(package, speccheck):
    """coid: comparison-operator-in-deptoken
    Test if specfile has comparison operator(==, >=) in deptoken.
    """
    output, test = speccheck
    pkg = get_tested_spec_package(package)
    test.check_spec(pkg)
    out = output.print_results(output.results)
    assert 'W: comparison-operator-in-deptoken Oneanotherthing>=1.0' in out
    assert 'W: comparison-operator-in-deptoken Onelastthing==2.0' in out
    assert 'W: comparison-operator-in-deptoken source-for-second-rpm' not in out


@pytest.mark.parametrize('package', ['spec/%autopatch-not-in-prep'])
def test_check_coid_is_found_with_single_space(package, speccheck):
    """coid: comparison-operator-in-deptoken
    Test if specfile has comparison operator(>=, <=) with single space in deptoken.
    """
    output, test = speccheck
    pkg = get_tested_spec_package(package)
    test.check_spec(pkg)
    out = output.print_results(output.results)
    assert 'W: comparison-operator-in-deptoken Someotherthinwithsinglespace<=' in out


@pytest.mark.parametrize('package', ['spec/%autosetup-not-in-prep'])
def test_check_coid_is_found_with_double_space(package, speccheck):
    """coid: comparison-operator-in-deptoken
    Test if specfile has comparison operator(>=, <=) with single space in deptoken.
    """
    output, test = speccheck
    pkg = get_tested_spec_package(package)
    test.check_spec(pkg)
    out = output.print_results(output.results)
    assert 'W: comparison-operator-in-deptoken /Something' not in out


@pytest.mark.parametrize('package', ['spec/unversioned-explicit-version'])
def test_check_unversioned_explicit_version(package, speccheck):
    """Test if specfile has Provides: tag."""
    output, test = speccheck
    pkg = get_tested_spec_package(package)
    test.check_spec(pkg)
    out = output.print_results(output.results)
    assert 'W: unversioned-explicit-provides someones-something=%{version}' in out


@pytest.mark.parametrize('package', ['spec/%autosetup-not-in-prep'])
def test_check_unversioned_explicit_version_not_found(package, speccheck):
    """Test if specfile has Provides: /something tag."""
    output, test = speccheck
    pkg = get_tested_spec_package(package)
    test.check_spec(pkg)
    out = output.print_results(output.results)
    assert 'W: unversioned-explicit-provides /something' not in out


@pytest.mark.parametrize('package', ['spec/SpecCheck2'])
def test_check_uev_not_applied(package, speccheck):
    """uev: unversioned-explicit-version
    1. Test if specfile does not have Provides: tag.
    2. Test if specfile does not have Obsoletes: tag.
    """
    output, test = speccheck
    pkg = get_tested_spec_package(package)
    test.check_spec(pkg)
    out = output.print_results(output.results)
    assert 'W: unversioned-explicit-provides' not in out


@pytest.mark.parametrize('package', ['spec/unversioned-explicit-obsoletes'])
def test_check_unversioned_explicit_obsoletes(package, speccheck):
    """Test if specfile has Obsoletes: tag."""
    output, test = speccheck
    pkg = get_tested_spec_package(package)
    test.check_spec(pkg)
    out = output.print_results(output.results)
    assert 'W: unversioned-explicit-obsoletes Something' in out


@pytest.mark.parametrize('package', ['spec/%autopatch-not-in-prep'])
def test_check_unversioned_explicit_obsoletes_not_found(package, speccheck):
    """Test if specfile has correct Obsoletes: tag
    and Provides: tag in specfile.
    """
    output, test = speccheck
    pkg = get_tested_spec_package(package)
    test.check_spec(pkg)
    out = output.print_results(output.results)
    assert 'W: unversioned-explicit-obsoletes %{name} <= %{version}' not in out
    assert 'W: unversioned-explicit-obsoletes %{name} = %{version}' not in out


@pytest.mark.parametrize('package', ['spec/SpecCheckTemp'])
def test_check_ueo_not_found(package, speccheck):
    """ueo: unversioned-explicit-obsoletes
    Test if specfile does has Obsoletes: /something.
    """
    output, test = speccheck
    pkg = get_tested_spec_package(package)
    test.check_spec(pkg)
    out = output.print_results(output.results)
    assert 'W: unversioned-explicit-obsoletes /something' not in out


@pytest.mark.parametrize('package', ['spec/macro-in-changelog'])
def test_check_macro_in_changelog(package, speccheck):
    """Test if specfile has macro in %changelog."""
    output, test = speccheck
    pkg = get_tested_spec_package(package)
    test.check_spec(pkg)
    out = output.print_results(output.results)
    assert 'W: macro-in-%changelog' in out


@pytest.mark.parametrize('package', ['spec/SpecCheck2'])
def test_check_macro_in_changelog_not_found(package, speccheck):
    """Test if specfile has macro in %changelog
    consisting of %%foo or %+foo or %.foo.
    """
    output, test = speccheck
    pkg = get_tested_spec_package(package)
    test.check_spec(pkg)
    out = output.print_results(output.results)
    assert 'W: macro-in-%changelog' not in out


@pytest.mark.parametrize('package', ['spec/SpecCheckTemp'])
def test_check_macro_in_changelog_not_applied(package, speccheck):
    """Test if specfile does not have macro in %changelog."""
    output, test = speccheck
    pkg = get_tested_spec_package(package)
    test.check_spec(pkg)
    out = output.print_results(output.results)
    assert 'W: macro-in-%changelog' not in out


@pytest.mark.parametrize('package', ['spec/libdir-macro-in-noarch-package'])
def test_check_libdir_macro_in_noarch_package(package, speccheck):
    """Test if specfile has _libdir macro in noarch package."""
    output, test = speccheck
    pkg = get_tested_spec_package(package)
    test.check_spec(pkg)
    out = output.print_results(output.results)
    assert 'W: libdir-macro-in-noarch-package' in out


@pytest.mark.parametrize('package', ['spec/mixed-use-of-spaces-and-tabs'])
def test_check_lmnp_not_applied(package, speccheck):
    """lmnp: libdir-macro-in-noarch-package
    Test if specfile does not have _libdir macro in noarch package.
    """
    output, test = speccheck
    pkg = get_tested_spec_package(package)
    test.check_spec(pkg)
    out = output.print_results(output.results)
    assert 'W: libdir-macro-in-noarch-package' not in out


@pytest.mark.parametrize('package', ['spec/deprecated-grep'])
def test_check_deprecated_grep(package, speccheck):
    """Test if specfile has direct use of grep or egrep or fgrep."""
    output, test = speccheck
    pkg = get_tested_spec_package(package)
    test.check_spec(pkg)
    out = output.print_results(output.results)
    assert 'W: deprecated-grep' in out


@pytest.mark.parametrize('package', ['spec/SpecCheckTemp'])
def test_check_deprecated_grep_not_found(package, speccheck):
    """Test if specfile has grep with -F or -E inside
    package, changelog, depscription, files macro
    """
    output, test = speccheck
    pkg = get_tested_spec_package(package)
    test.check_spec(pkg)
    out = output.print_results(output.results)
    assert 'W: deprecated-grep' not in out


@pytest.mark.parametrize('package', ['spec/SpecCheck2'])
def test_check_deprecated_grep_not_applied(package, speccheck):
    """Test if specfile has no use of egrep/fgrep or egrep/fgrep with -E or -F."""
    output, test = speccheck
    pkg = get_tested_spec_package(package)
    test.check_spec(pkg)
    out = output.print_results(output.results)
    assert 'W: deprecated-grep' not in out


# TODO: Add test for non-standard-Group


@pytest.mark.parametrize('package', ['spec/macro-in-comment'])
def test_check_macro_in_comment(package, speccheck):
    """Test if specfile has macro in comment."""
    output, test = speccheck
    pkg = get_tested_spec_package(package)
    test.check_spec(pkg)
    out = output.print_results(output.results)
    assert 'W: macro-in-comment' in out


@pytest.mark.parametrize('package', ['spec/%autosetup-not-in-prep'])
def test_check_macro_in_comment_not_found(package, speccheck):
    """Test if specfile has comment in macro."""
    output, test = speccheck
    pkg = get_tested_spec_package(package)
    test.check_spec(pkg)
    out = output.print_results(output.results)
    assert 'W: macro-in-comment' not in out


@pytest.mark.parametrize('package', ['spec/SpecCheck2'])
def test_check_macro_in_comment_not_applied(package, speccheck):
    """Test if specfile does not have macro inside a comment."""
    output, test = speccheck
    pkg = get_tested_spec_package(package)
    test.check_spec(pkg)
    out = output.print_results(output.results)
    assert 'W: macro-in-comment' not in out


@pytest.mark.parametrize('package', ['spec/no-buildroot-tag'])
def test_check_no_build_root_tag(package, speccheck):
    """Test if specfile does not have BuildRoot tag."""
    output, test = speccheck
    pkg = get_tested_spec_package(package)
    test.check_spec(pkg)
    out = output.print_results(output.results)
    assert 'W: no-buildroot-tag' in out


@pytest.mark.parametrize('package', ['spec/SpecCheck2'])
def test_check_no_build_root_tag_not_applied(package, speccheck):
    """Test if specfile has BuildRoot tag."""
    output, test = speccheck
    pkg = get_tested_spec_package(package)
    test.check_spec(pkg)
    out = output.print_results(output.results)
    assert 'W: no-buildroot-tag' not in out


@pytest.mark.parametrize('package', ['spec/no-%%%s-section'])
def test_check_no_essential_section(package, speccheck):
    """Test for no-%%%s-section check
    Test if specfile does not have essential section tag.
    """
    output, test = speccheck
    pkg = get_tested_spec_package(package)
    test.check_spec(pkg)
    out = output.print_results(output.results)
    assert 'W: no-%prep-section' in out
    assert 'W: no-%install-section' in out
    assert 'W: no-%build-section' in out


@pytest.mark.parametrize('package', ['spec/SpecCheck2'])
def test_check_no_essential_section_not_applied(package, speccheck):
    """Test for no-%%%s-section check
    Test if specfile has all essential section tag.
    """
    output, test = speccheck
    pkg = get_tested_spec_package(package)
    test.check_spec(pkg)
    out = output.print_results(output.results)
    assert 'W: no-%prep-section' not in out
    assert 'W: no-%install-section' not in out
    assert 'E: superfluous-%clean-section' in out
    assert 'W: no-%build-section' not in out


@pytest.mark.parametrize('package', ['spec/more-than-one-%changelog'])
def test_check_more_than_one_changelog_section(package, speccheck):
    """Test if specfile has more than one changelog section."""
    output, test = speccheck
    pkg = get_tested_spec_package(package)
    test.check_spec(pkg)
    out = output.print_results(output.results)
    assert 'W: more-than-one-%changelog-section' in out


@pytest.mark.parametrize('package', ['spec/SpecCheck2'])
def test_check_mtocs_not_applied(package, speccheck):
    """mtocs: more-than-one-%changelog-section
    Test if specfile does not have more than one changelog section.
    """
    output, test = speccheck
    pkg = get_tested_spec_package(package)
    test.check_spec(pkg)
    out = output.print_results(output.results)
    assert 'W: more-than-one-%changelog-section' not in out


@pytest.mark.parametrize('package', ['spec/lib-package-without-%mklibname'])
def test_check_lib_package_without_mklibname(package, speccheck):
    """Test if specfile has lib pacakge without %mklibname."""
    output, test = speccheck
    pkg = get_tested_spec_package(package)
    test.check_spec(pkg)
    out = output.print_results(output.results)
    assert 'E: lib-package-without-%mklibname' in out


@pytest.mark.parametrize('package', ['spec/SpecCheck2'])
def test_check_lpwm_not_applied(package, speccheck):
    """lpwm: lib-package-without-%mklibname
    Test if specfile does not have lib pacakge without %mklibname."""
    output, test = speccheck
    pkg = get_tested_spec_package(package)
    test.check_spec(pkg)
    out = output.print_results(output.results)
    assert 'E: lib-package-without-%mklibname' not in out


@pytest.mark.parametrize('package', ['spec/depscript-without-disabling-depgen'])
def test_check_depscript_without_disabling_depgen(package, speccheck):
    """Test if specfile has define __find_provides/requires."""
    output, test = speccheck
    pkg = get_tested_spec_package(package)
    test.check_spec(pkg)
    out = output.print_results(output.results)
    assert 'W: depscript-without-disabling-depgen' in out


@pytest.mark.parametrize('package', ['spec/SpecCheckTemp'])
def test_check_depscript_without_disabling_depgen_not_found(package, speccheck):
    """Test if specfile has define __find_provides/requires with
    %define _use_internal_dependency_generator set to 0.
    """
    output, test = speccheck
    pkg = get_tested_spec_package(package)
    test.check_spec(pkg)
    out = output.print_results(output.results)
    assert 'W: depscript-without-disabling-depgen' not in out


@pytest.mark.parametrize('package', ['spec/SpecCheck2'])
def test_check_dwdd_not_applied(package, speccheck):
    """dwdd: depscript-without-disabling-depgen
    Test if specfile does not have define __find_provides/requires."""
    output, test = speccheck
    pkg = get_tested_spec_package(package)
    test.check_spec(pkg)
    out = output.print_results(output.results)
    assert 'W: depscript-without-disabling-depgen' not in out


@pytest.mark.parametrize('package', ['spec/patch-fuzz-is-changed'])
def test_check_patch_fuzz_is_changed(package, speccheck):
    """Test if specfile has internal/default patch fuzz value changed as
    %define _default_patch_fuzz >= 0.
    """
    output, test = speccheck
    pkg = get_tested_spec_package(package)
    test.check_spec(pkg)
    out = output.print_results(output.results)
    assert 'W: patch-fuzz-is-changed' in out


@pytest.mark.parametrize('package', ['spec/SpecCheckTemp'])
def test_check_patch_fuzz_is_changed_not_found(package, speccheck):
    output, test = speccheck
    pkg = get_tested_spec_package(package)
    test.check_spec(pkg)
    out = output.print_results(output.results)
    assert 'W: patch-fuzz-is-changed' not in out


@pytest.mark.parametrize('package', ['spec/macro-in-comment'])
def test_check_patch_fuzz_is_changed_not_applied(package, speccheck):
    output, test = speccheck
    pkg = get_tested_spec_package(package)
    test.check_spec(pkg)
    out = output.print_results(output.results)
    assert 'W: patch-fuzz-is-changed' not in out


@pytest.mark.parametrize('package', ['spec/mixed-use-of-spaces-and-tabs'])
def test_check_mixed_use_of_spaces_and_tabs(package, speccheck):
    """Test if specfile has mix use of space and tabs."""
    output, test = speccheck
    pkg = get_tested_spec_package(package)
    test.check_spec(pkg)
    out = output.print_results(output.results)
    assert 'W: mixed-use-of-spaces-and-tabs' in out


@pytest.mark.parametrize('package', ['spec/SpecCheck2'])
def test_check_mixed_use_of_spaces_and_tabs_not_applied(package, speccheck):
    """Test if specfile does not have mix use of space and tabs."""
    output, test = speccheck
    pkg = get_tested_spec_package(package)
    test.check_spec(pkg)
    out = output.print_results(output.results)
    assert 'W: mixed-use-of-spaces-and-tabs' not in out


@pytest.mark.parametrize('package', ['spec/%ifarch-applied-patch'])
def test_check_ifarch_applied_patch(package, speccheck):
    """Test if specfile has no patch in %ifarch block."""
    output, test = speccheck
    pkg = get_tested_spec_package(package)
    test.check_spec(pkg)
    out = output.print_results(output.results)
    assert 'W: %ifarch-applied-patch' in out


@pytest.mark.parametrize('package', ['spec/mixed-use-of-spaces-and-tabs'])
def test_check_ifarch_applied_not_enforced(package, speccheck):
    """Test if specfile has patch in %ifarch block."""
    output, test = speccheck
    pkg = get_tested_spec_package(package)
    test.check_spec(pkg)
    out = output.print_results(output.results)
    assert 'W: %ifarch-applied-patch' not in out


@pytest.mark.parametrize('package', ['spec/patch-not-applied'])
def test_check_patch_not_applied(package, speccheck):
    """Test if specfile does not have all patch applied."""
    output, test = speccheck
    pkg = get_tested_spec_package(package)
    test.check_spec(pkg)
    out = output.print_results(output.results)
    assert 'W: patch-not-applied' in out


@pytest.mark.parametrize('package', ['spec/mixed-use-of-spaces-and-tabs'])
def test_check_patch_not_found(package, speccheck):
    """Test if specfile have all patch applied by %autopatch."""
    output, test = speccheck
    pkg = get_tested_spec_package(package)
    test.check_spec(pkg)
    out = output.print_results(output.results)
    assert 'W: patch-not-applied' not in out


@pytest.mark.parametrize('package', ['spec/mixed-use-of-spaces-and-tabs'])
def test_check_patch_not_applied_not_enforced(package, speccheck):
    """Test if specfile has all patch applied."""
    output, test = speccheck
    pkg = get_tested_spec_package(package)
    test.check_spec(pkg)
    out = output.print_results(output.results)
    assert 'W: patch-not-applied' not in out


# TODO: Add specfile-error test.


@pytest.mark.parametrize('package', ['spec/SpecCheck2'])
def test_check_invalid_url(package, speccheck):
    """Test if specfile has invalid url."""
    output, test = speccheck
    pkg = get_tested_spec_package(package)
    test.check_spec(pkg)
    out = output.print_results(output.results)
    assert 'W: invalid-url' in out


@pytest.mark.parametrize('package', ['spec/mixed-use-of-spaces-and-tabs'])
def test_check_invalid_url_not_applied(package, speccheck):
    """Test if specfile does not have invalid url."""
    output, test = speccheck
    pkg = get_tested_spec_package(package)
    test.check_spec(pkg)
    out = output.print_results(output.results)
    assert 'W: invalid-url' not in out
