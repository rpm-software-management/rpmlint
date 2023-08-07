from pathlib import Path
import platform
import re

from packaging.requirements import InvalidRequirement, Requirement
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


EGG_INFO_RE = re.compile('.*egg-info$')
PYC_RE = re.compile(r'cpython-(\d+)')


class PythonCheck(AbstractFilesCheck):
    def __init__(self, config, output):
        super().__init__(config, output, r'.*')

    def check_binary(self, pkg):
        self._pyc_version = None
        super().check_binary(pkg)

    def check_file(self, pkg, filename):
        # egg-info format
        if filename.endswith('egg-info/requires.txt'):
            self._check_requires_txt(pkg, filename)
        # dist-info format
        if filename.endswith('dist-info/METADATA'):
            self._check_requires_metadata(pkg, filename)

        if EGG_INFO_RE.match(filename):
            self._check_egginfo(pkg, filename)

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

        if filename.endswith('pyc'):
            # Check for .pyc from different python versions in the same package
            self._check_multiple_python_pyc(pkg, filename)

    def _check_multiple_python_pyc(self, pkg, filename):
        """
        """
        search = PYC_RE.search(filename)
        if not search:
            return

        version = search.group(1)
        if self._pyc_version is None:
            # First pyc file, just store the version
            self._pyc_version = version
        elif self._pyc_version != version:
            self.output.add_info('W', pkg, 'python-pyc-multiple-versions',
                                 'expected:', self._pyc_version, filename)

    def _check_egginfo(self, pkg, filename):
        """
        Check type of egg-info metadata and check Requires against egg-info
        metadata if applicable.
        """

        filepath = Path(pkg.dir_name() or '/', filename.lstrip('/'))
        # Check for (deprecated) distutils style metadata.
        if filepath.is_file():
            self.output.add_info('E', pkg, ERRS['egg-distutils'], filename)

    def _check_requires_txt(self, pkg, filename):
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

                # Ignore broken requirements
                try:
                    req = Requirement(requirement)
                except InvalidRequirement:
                    continue

                requirements.append(req)

        self._check_requirements(pkg, requirements)

    def _check_requires_metadata(self, pkg, filename):
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

                # Ignore broken requirements
                try:
                    req = Requirement(requirement)
                except InvalidRequirement:
                    continue

                requirements.append(req)

        self._check_requirements(pkg, requirements)

    def _check_requirements(self, pkg, requirements):
        """
        Check mismatch between the list of requirements and the rpm
        declared requires.
        """

        env = {
            'python_version': '.'.join(platform.python_version_tuple()[:2]),
            'os_name': 'posix',
            'platform_system': 'Linux',
        }

        # Look for python version
        for req in pkg.requires:
            if req.name == 'python(abi)':
                _, pyv, _ = req.version
                env['python_version'] = pyv
                break

        # Check for missing requirements
        for req in requirements:
            if req.marker:
                # Ignore extra requires
                if 'extra' in str(req.marker):
                    continue
                # Ignore not env requirements
                if not req.marker.evaluate(environment=env):
                    continue

            self._check_require(pkg, req)

        # Check for python requirement not needed
        self._check_leftover_requirements(pkg, requirements)

    def _check_require(self, pkg, requirement):
        """
        Look for the module_name in the package requirements, looking
        for common python rpm package names like python-foo,
        python3-foo, etc.
        """

        names = self._module_names(requirement.name, extras=requirement.extras)

        # Add pythonX-foo variants
        names += [f'python\\d*-{re.escape(i)}' for i in names]
        regex = '|'.join(names)
        # Support complex requirements like
        # (python310-jupyter-server >= 1.15 with python310-jupyter-server < 3)
        version_req = r'\s*(==|<|<=|>|>=)\s*[\w.]+\s*'
        richop_req = r'\s+(and|or|if|unless|else|with|without)\s+.*'
        try:
            regex = re.compile(rf'^\(?({regex})({version_req})?({richop_req})?\)?\s*$', re.IGNORECASE)
        except re.error:
            # Bad regular expression, it could be a name with weird
            # characters
            return False

        for req in pkg.req_names:
            if regex.match(req):
                return True

        self.output.add_info('W', pkg, 'python-missing-require', requirement.name)
        return False

    def _check_leftover_requirements(self, pkg, requirements):
        """
        Look for python-foo requirements in the rpm package that are
        not in the list of requirements of this package.
        """

        pythonpac = re.compile(r'^python\d*-(?P<name>.+)$')
        reqs = set()
        for i in requirements:
            for n in self._module_names(i.name, extras=i.extras):
                reqs.add(n.lower())

        for req in pkg.req_names:
            match = pythonpac.match(req)
            if not match:
                continue

            module_name = match.group('name').strip().lower()
            # ignore python-base, python-devel packages, that are
            # not python modules
            if module_name in ('base', 'devel'):
                continue

            names = set(self._module_names(module_name))

            if not (names & reqs):
                self.output.add_info('W', pkg, 'python-leftover-require', req)

    def _module_names(self, module_name, extras=None):
        """
        Return a list with possible variants of the module name,
        replacing "-", "_".
        """

        # Name variants changing '-' with '_'
        variants = []
        variants.append(module_name.replace('-', '_'))
        variants.append(module_name.replace('_', '-'))

        # Look also for python-MOD-EXTRA
        if extras:
            for e in extras:
                variants += self._module_names(f'{module_name}-{e}')

        return [
            module_name,
            *variants,
        ]
