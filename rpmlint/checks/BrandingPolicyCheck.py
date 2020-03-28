import re

from rpm import RPMSENSE_EQUAL, RPMSENSE_GREATER
from rpmlint.checks.AbstractCheck import AbstractCheck


class BrandingPolicyCheck(AbstractCheck):
    # libreoffice-branding-upstream
    # terminology-theme-openSUSE
    re_branding = re.compile(r'(?P<name>\S+)-(?P<type>branding|theme)-(?P<flavor>\S+)')
    re_branding_generic = re.compile(r'(?P<name>\S+)-(?P<type>branding|theme)')
    re_icon_theme = re.compile(r'(?P<name>\S+)-icon-theme')

    def _check_conflicts(self, pkg, branding_name):
        """Check the conflict on the generic branding package name"""
        pkg_conflicts = [x.name for x in pkg.conflicts]
        if branding_name not in pkg_conflicts:
            self.output.add_info('E', pkg, 'branding-conflicts-missing', branding_name)

    def _check_versioned_branding_requires(self, pkg):
        """Check the requires to contain only unflavored branding requires with version"""
        for require in pkg.requires:
            # we have direct branding dep instead of the provide letting us decide
            if self.re_branding.match(require.name):
                self.output.add_info('E', pkg, 'branding-requires-specific-flavor', require.name)
                continue
            # we have proper generic dep it should be versioned either >= or = are okay
            # Best case scenario:
            """
            Requires: %{name}-branding = %{version}
            ...
            %package branding-upstream
            Provides: %{name}-branding = %{version}
            """
            if self.re_branding_generic.match(require.name):
                if require.flags != RPMSENSE_EQUAL and require.flags != RPMSENSE_GREATER and require.flags != RPMSENSE_GREATER + RPMSENSE_EQUAL:
                    self.output.add_info('E', pkg, 'branding-requires-unversioned', require.name)

    def _check_supplements(self, pkg, branding_pkg, branding_name):
        """Verify we have only one supplement on the branding and packagename"""
        pkg_supplements = [x.name for x in pkg.supplements]
        correct_supplement = f'({branding_pkg} and {branding_name})'
        if correct_supplement not in pkg_supplements:
            self.output.add_info('E', pkg, 'branding-supplements-missing', correct_supplement)

    def _check_provides(self, pkg, branding_name):
        """Verify we have provides on branding symbol with proper version"""
        branding_provide = None
        for provide in pkg.provides:
            if provide.name == branding_name:
                branding_provide = provide
                break
        if not branding_provide:
            self.output.add_info('E', pkg, 'branding-provides-missing')
        else:
            if (len(branding_provide) < 2 or branding_provide.flags != RPMSENSE_EQUAL):
                self.output.add_info('E', pkg, 'branding-provides-unversioned', branding_provide.name)

    def _check_empty_vars(self, pkg):
        """The keywords like recommends/suggests/enhances should be empty on the branding package"""
        for r in pkg.recommends:
            self.output.add_info('W', pkg, 'branding-excessive-recommends', r.name)
        for r in pkg.suggests:
            self.output.add_info('W', pkg, 'branding-excessive-suggests', r.name)
        for r in pkg.enhances:
            self.output.add_info('W', pkg, 'branding-excessive-enhances', r.name)

    def check(self, pkg):
        if pkg.is_source:
            return

        # check dependencies of all packages if they do not pull branding wrongly
        branding_match = self.re_branding.match(pkg.name)
        if not branding_match:
            # check dependencies of all packages if they do not pull branding wrongly
            self._check_versioned_branding_requires(pkg)
        else:
            # we happen to have branding package so verify it provides/does all the proper stuff
            branding_pkg = branding_match.group('name')
            branding_flavor = branding_match.group('flavor')
            branding_type = branding_match.group('type')
            branding_type_flavor = f'{branding_type}-{branding_flavor}'
            generic_branding_name = f'{branding_pkg}-{branding_type}'

            self._check_conflicts(pkg, generic_branding_name)
            self._check_supplements(pkg, branding_pkg, branding_type_flavor)
            self._check_provides(pkg, generic_branding_name)
            self._check_empty_vars(pkg)
