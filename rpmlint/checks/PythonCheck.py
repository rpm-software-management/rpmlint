import os
import re

from rpmlint.checks.AbstractCheck import AbstractFilesCheck

# Warning messages
WARNS = {'tests': 'python-tests-in-package',
         'doc': 'python-doc-in-package'}

# Error messages
ERRS = {'egg-distutils': 'python-egg-info-distutils-style',
        'tests': 'python-tests-in-site-packages',
        'doc': 'python-doc-in-site-packages',
        'src': 'python-src-in-site-packages'}

# Paths that shouldn't be in any packages, ever, because they clobber global
# name space.
ERR_PATHS = {'/usr/lib[^/]*/python[^/]*/site-packages/tests?$': ERRS['tests'],
             '/usr/lib[^/]*/python[^/]*/site-packages/docs?$': ERRS['doc'],
             '/usr/lib[^/]*/python[^/]*/site-packages/src$': ERRS['src']}

# Paths that shouldn't be in any packages, but might need to be under
# sufficiently special circumstances.
WARN_PATHS = {'/usr/lib[^/]*/python[^/]*/site-packages/[^/]+/tests?$': WARNS['tests'],
              '/usr/lib[^/]*/python[^/]*/site-packages/[^/]+/docs?$': WARNS['doc']}


class PythonCheck(AbstractFilesCheck):
    def __init__(self, config, output):
        super().__init__(config, output, r'.*')

    def check_file(self, pkg, filename):
        egg_info_re = re.compile('.*egg-info$')

        if egg_info_re.match(filename):
            self.check_egginfo(pkg, filename)

        for path in WARN_PATHS:
            path_re = re.compile(path)

            if path_re.match(filename):
                self.output.add_info('W', pkg, WARN_PATHS[path], filename)

        for path in ERR_PATHS:
            path_re = re.compile(path)

            if path_re.match(filename):
                self.output.add_info('E', pkg, ERR_PATHS[path], filename)

    def check_egginfo(self, pkg, filename):
        """
        Check type of egg-info metadata and check Requires against egg-info
        metadata if applicable.
        """
        # Check for (deprecated) distutils style metadata.
        if os.path.isfile(os.path.join(pkg.dirName(), filename.lstrip('/'))):
            self.output.add_info('E', pkg, ERRS['egg-distutils'], filename)
