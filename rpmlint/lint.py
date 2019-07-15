import importlib
import sys
from tempfile import gettempdir

from rpmlint.config import Config
from rpmlint.filter import Filter
from rpmlint.helpers import print_warning
from rpmlint.pkg import FakePkg, Pkg


class Lint(object):
    """
    Generic object handling the basic rpmlint operations
    """

    def __init__(self, options):
        # initialize configuration
        self.checks = {}
        self.options = options
        self.packages_checked = 0
        self.specfiles_checked = 0
        if options['config']:
            self.config = Config(options['config'])
        else:
            self.config = Config()
        if options['rpmlintrc']:
            self.config.load_rpmlintrc(options['rpmlintrc'])
        if options['verbose']:
            self.config.info = options['verbose']
        if not self.config.configuration['ExtractDir']:
            self.config.configuration['ExtractDir'] = gettempdir()
        # initialize output buffer
        self.output = Filter(self.config)
        # preload the check list
        self.load_checks()

    def run(self):
        # if we just want to print config, do so and leave
        if self.options['print_config']:
            self.print_config()
            return 0
        # just explain the error and abort too
        if self.options['explain']:
            self.print_explanation(self.options['explain'])
            return 0
        # if no exclusive option is passed then just loop over all the
        # arguments that are supposed to be either rpm or spec files
        self.validate_files(self.options['rpmfile'])
        print(self.output.print_results(self.output.results))
        print('{} packages and {} specfiles checked; {} errors, {} warnings'.format(self.packages_checked, self.specfiles_checked, self.output.printed_messages['E'], self.output.printed_messages['W']))
        if self.output.badness_threshold > 0 and self.output.score > self.output.badness_threshold:
            print_warning(f'(none): E: Badness {self.output.score} exceeeds threshold {self.output.badness_threshold}, aborting.')
            return 66
        if self.output.printed_messages['E'] > 0:
            return 64
        return 0

    def info_error(self, errors):
        """
        Print details for specified error/s.
        """
        self.output.info = True
        for e in sorted(errors):
            print(f'{e}:')
            print(self.output.get_description(e))

    def validate_files(self, files):
        """
        Run all the check for passed file list
        """
        if not files:
            print('There are no files to process nor additional arguments.', file=sys.stderr)
            print('Nothing to do, aborting.', file=sys.stderr)
            return
        for pkg in files:
            self.validate_file(pkg)

    def validate_file(self, pname):
        try:
            if pname.suffix == '.rpm' or pname.suffix == '.spm':
                with Pkg(pname, self.config.configuration['ExtractDir']) as pkg:
                    self.run_checks(pkg)
                    self.packages_checked += 1
            elif pname.suffix == '.spec':
                with FakePkg(pname) as pkg:
                    self.run_spec_checks(pkg)
                    self.specfiles_checked += 1
        except Exception as e:
            print_warning(f'(none): E: while reading {pname}: {e}')

    def run_checks(self, pkg):
        for checker in self.checks:
            self.checks[checker].check(pkg)

    def run_spec_checks(self, pkg):
        for checker in self.checks:
            self.checks[checker].check_spec(pkg)

    def print_config(self):
        """
        Just output the current configuration
        """
        self.config.print_config()

    def print_explanation(self, message):
        """
        Print out detailed explanation for the specified message
        """
        explanation = self.output.get_description(message)
        if explanation:
            print(explanation)
        else:
            print(f'Unknown message {message}, or no known description')

    def load_checks(self):
        """
        Load all checks based on the config, skipping those already loaded
        SingletonTM
        """

        for check in self.config.configuration['Checks']:
            if check in self.checks:
                continue
            self.checks[check] = self.load_check(check)

    def load_check(self, name):
        """Load a (check) module by its name, unless it is already loaded."""
        module = importlib.import_module(f'.{name}', package='rpmlint.checks')
        klass = getattr(module, name)
        obj = klass(self.config, self.output)
        return obj
