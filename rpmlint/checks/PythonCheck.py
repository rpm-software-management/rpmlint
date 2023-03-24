from pathlib import Path
import re

from rpmlint.checks.AbstractCheck import AbstractFilesCheck

# Warning messages
WARNS = {
    'doc': 'python-doc-in-package',
}

# Error messages
ERRS = {
    'egg-distutils': 'python-egg-info-distutils-style',
    'tests': 'python-tests-in-site-packages',
    'doc': 'python-doc-in-site-packages',
    'src': 'python-src-in-site-packages',
}

SITELIB_RE = '/usr/lib[^/]*/python[^/]*/site-packages'

# Paths that shouldn't be in any packages, ever, because they clobber global
# name space.
ERR_PATHS = [
    (re.compile(f'{SITELIB_RE}/tests?$'), 'tests'),
    (re.compile(f'{SITELIB_RE}/docs?$'), 'doc'),
    (re.compile(f'{SITELIB_RE}/src$'), 'src'),
]

# Paths that shouldn't be in any packages, but might need to be under
# sufficiently special circumstances.
WARN_PATHS = [
    (re.compile(f'{SITELIB_RE}/[^/]+/docs?$'), 'doc'),
]


class PythonCheck(AbstractFilesCheck):
    def __init__(self, config, output):
        super().__init__(config, output, r'.*')

    def check_file(self, pkg, filename):
        # egg-info format
        if filename.endswith('egg-info/requires.txt'):
            self.check_requires_txt(pkg, filename)
        # dist-info format
        if filename.endswith('dist-info/METADATA'):
            self.check_requires_metadata(pkg, filename)

        egg_info_re = re.compile('.*egg-info$')

        if egg_info_re.match(filename):
            self.check_egginfo(pkg, filename)

        for path_re, key in WARN_PATHS:
            if path_re.match(filename):
                if key == 'doc':
                    # Check for __init__.py file inside doc, maybe this is a
                    # module, not documentation
                    module_file = f'{filename}/__init__.py'
                    if module_file in pkg.files.keys():
                        continue
                self.output.add_info('W', pkg, WARNS[key], filename)

        for path_re, key in ERR_PATHS:
            if path_re.match(filename):
                self.output.add_info('E', pkg, ERRS[key], filename)

    def check_egginfo(self, pkg, filename):
        """
        Check type of egg-info metadata and check Requires against egg-info
        metadata if applicable.
        """

        filepath = Path(pkg.dir_name() or '/', filename.lstrip('/'))
        # Check for (deprecated) distutils style metadata.
        if filepath.is_file():
            self.output.add_info('E', pkg, ERRS['egg-distutils'], filename)

    def check_requires_txt(self, pkg, filename):
        """
        Look for all requirements defined in the python package and
        compare with the requirements defined in the rpm package
        """

        filepath = Path(pkg.dir_name() or '/', filename.lstrip('/'))
        requirements = []
        with filepath.open() as f:
            for requirement in f.readlines():
                # Ignore sections, just check for default requirements
                if requirement.startswith('['):
                    break

                # Ignore version limitations for now
                requirement, *_ = re.split('[<>=!~]', requirement)
                requirements.append(requirement)

        self._check_requirements(pkg, requirements)

    def check_requires_metadata(self, pkg, filename):
        """
        Look for all requirements defined in the python package and
        compare with the requirements defined in the rpm package
        """

        regex = re.compile(r'^Requires-Dist: (?P<req>.*)$', re.IGNORECASE)

        filepath = Path(pkg.dir_name() or '/', filename.lstrip('/'))
        requirements = []
        with filepath.open() as f:
            for requirement in f.readlines():
                match = regex.match(requirement)
                if not match:
                    continue

                requirement = match.group('req')
                # Ignore extra requires
                if 'extra ==' in requirement:
                    continue
                # Ignore windows platform
                if 'platform_system == "Windows"' in requirement:
                    continue

                # Ignore version limitations for now
                requirement, *_ = re.split('[ <>=!~]', requirement)
                requirements.append(requirement)

        self._check_requirements(pkg, requirements)

    def _check_requirements(self, pkg, requirements):
        """
        Check mismatch between the list of requirements and the rpm
        declared requires.
        """

        # Check for missing requirements
        for req in requirements:
            self._check_require(pkg, req.strip())

        # Check for python requirement not needed
        self._check_leftover_requirements(pkg, requirements)

    def _check_require(self, pkg, module_name):
        """
        Look for the module_name in the package requirements, looking
        for common python rpm package names like python-foo,
        python3-foo, etc.
        """

        if not module_name:
            return True

        names = self._module_names(module_name)
        # Add pythonX-foo variants
        names += [f'python\\d*-{re.escape(i)}' for i in names]
        regex = '|'.join(names)
        regex = re.compile(f'^({regex})$', re.IGNORECASE)

        for req in pkg.req_names:
            if regex.match(req):
                return True

        self.output.add_info('W', pkg, 'python-missing-require', module_name)
        return False

    def _check_leftover_requirements(self, pkg, requirements):
        """
        Look for python-foo requirements in the rpm package that are
        not in the list of requirements of this package.
        """

        pythonpac = re.compile(r'^python\d*-(?P<name>.+)$')
        requirements = {i.strip().lower() for i in requirements}

        for req in pkg.req_names:
            match = pythonpac.match(req)
            if not match:
                continue

            module_name = match.group('name').strip().lower()
            names = set(self._module_names(module_name))

            if not (names & requirements):
                self.output.add_info('W', pkg, 'python-leftover-require', req)

    def _module_names(self, module_name):
        """
        Return a list with possible variants of the module name,
        replacing "-", "_".
        """
        return [
            module_name,
            module_name.replace('-', '_'),
            module_name.replace('_', '-'),
        ]
