import cProfile
import importlib
import operator
from pstats import Stats
import sys
from tempfile import gettempdir
import time

from rpmlint.color import Color
from rpmlint.config import Config
from rpmlint.filter import Filter
from rpmlint.helpers import print_warning, string_center
from rpmlint.pkg import FakePkg, getInstalledPkgs, Pkg
from rpmlint.version import __version__


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
        self.check_duration = {}
        if options['config']:
            self.config = Config(options['config'])
        else:
            self.config = Config()
        if options['profile']:
            self.profile = cProfile.Profile()
            self.profile.enable()
        else:
            self.profile = None
        self._load_rpmlintrc()
        if options['verbose']:
            self.config.info = options['verbose']
        if options['strict']:
            self.config.strict = options['strict']
        if options['permissive']:
            self.config.permissive = options['permissive']
        if not self.config.configuration['ExtractDir']:
            self.config.configuration['ExtractDir'] = gettempdir()
        # initialize output buffer
        self.output = Filter(self.config)
        # preload the check list if we not print config
        # some of the config values are transformed e.g. to regular
        # expressions
        if not self.options['print_config']:
            self.load_checks()

    def _run(self):
        start = time.monotonic()
        retcode = 0
        # if we just want to print config, do so and leave
        if self.options['print_config']:
            self.print_config()
            return retcode
        # just explain the error and abort too
        if self.options['explain']:
            self.print_explanation(self.options['explain'], self.config)
            return retcode
        # if there are installed arguments just load them up as extra
        # items to the rpmfile option
        if self.options['installed']:
            self.validate_installed_packages(self._load_installed_rpms(self.options['installed']))
        # if no exclusive option is passed then just loop over all the
        # arguments that are supposed to be either rpm or spec files
        self.validate_files(self.options['rpmfile'])
        self._print_header()
        print(self.output.print_results(self.output.results, self.config),
              end='')
        quit_color = Color.Bold
        if self.output.printed_messages['W'] > 0:
            quit_color = Color.Yellow
        if self.output.badness_threshold > 0 and self.output.score > self.output.badness_threshold:
            msg = string_center(f'Badness {self.output.score} exceeds threshold {self.output.badness_threshold}, aborting.', '-')
            print(f'{Color.Red}{msg}{Color.Reset}')
            quit_color = Color.Red
            retcode = 66
        elif self.output.printed_messages['E'] > 0 and not self.config.permissive:
            quit_color = Color.Red
            retcode = 64

        self._maybe_print_reports()

        duration = time.monotonic() - start
        msg = string_center(f'{self.packages_checked} packages and {self.specfiles_checked} specfiles checked; '
                            f'{self.output.printed_messages["E"]} errors, {self.output.printed_messages["W"]} warnings, '
                            f'{self.output.score} badness; has taken {duration:.1f} s', '=')
        print(f'{quit_color}{msg}{Color.Reset}')

        return retcode

    def run(self):
        try:
            return self._run()
        except KeyboardInterrupt as e:
            self._maybe_print_reports()
            raise e

    def _maybe_print_reports(self):
        if self.options['time_report']:
            self._print_time_report()
        if self.profile:
            self._print_cprofile()

    def _get_color_time_report_value(self, fraction):
        if fraction > 25:
            color = Color.Red
        elif fraction > 5:
            color = Color.Yellow
        else:
            color = ''
        return f'{color}{fraction:17.1f}{Color.Reset}'

    def _print_time_report(self):
        THRESHOLD = 1
        total = sum(self.check_duration.values())
        checked_files = [check.checked_files for check in self.checks.values() if check.checked_files]
        total_checked_files = max(checked_files) if checked_files else ''
        print(f'\n{Color.Bold}Check time report{Color.Reset} (>{THRESHOLD}%):')

        print(f'{Color.Bold}    {"Check":32s} {"Duration (in s)":>12} {"Fraction (in %)":>17}  Checked files{Color.Reset}')
        for check, duration in sorted(self.check_duration.items(), key=operator.itemgetter(1), reverse=True):
            fraction = 100.0 * duration / total
            if fraction < THRESHOLD:
                continue
            checked_files = self.checks[check].checked_files
            if not checked_files:
                checked_files = ''
            print(f'    {check:32s} {duration:15.2f} {self._get_color_time_report_value(fraction)} {checked_files:>14}')
        print(f'    {"TOTAL":32s} {total:15.2f} {100:17.2f} {total_checked_files:>14}')

    def _print_cprofile(self):
        N = 30
        print(f'\n{Color.Bold}cProfile report:{Color.Reset}')
        self.profile.disable()
        stats = Stats(self.profile)
        stats.sort_stats('cumulative').print_stats(N)
        print('========================================================')
        stats.sort_stats('ncalls').print_stats(N)
        print('========================================================')
        stats.sort_stats('tottime').print_stats(N)

    def _load_installed_rpms(self, packages):
        existing_packages = []
        for name in packages:
            pkg = getInstalledPkgs(name)
            if pkg:
                existing_packages.extend(pkg)
            else:
                print_warning(f'(none): E: there is no installed rpm "{name}".')
        return existing_packages

    def _load_rpmlintrc(self):
        """
        Load rpmlintrc from argument or load up from folder
        """
        if self.options['rpmlintrc']:
            self.config.load_rpmlintrc(self.options['rpmlintrc'])
        else:
            # load only from the same folder specname.rpmlintrc or specname-rpmlintrc
            # do this only in a case where there is one folder parameter or one file
            # to avoid multiple folders handling
            rpmlintrc = []
            if not len(self.options['rpmfile']) == 1:
                return
            pkg = self.options['rpmfile'][0]
            if pkg.is_file():
                pkg = pkg.parent
            rpmlintrc += sorted(pkg.glob('*.rpmlintrc'))
            rpmlintrc += sorted(pkg.glob('*-rpmlintrc'))
            if len(rpmlintrc) > 1:
                # multiple rpmlintrcs are highly undesirable
                print_warning('There are multiple items to be loaded for rpmlintrc, ignoring them: {}.'.format(' '.join(map(str, rpmlintrc))))
            elif len(rpmlintrc) == 1:
                self.options['rpmlintrc'] = rpmlintrc[0]
                self.config.load_rpmlintrc(rpmlintrc[0])

    def _print_header(self):
        """
        Print out header information about the state of the
        rpmlint prior printing out the check report.
        """
        intro = string_center('rpmlint session starts', '=')
        print(f'{Color.Bold}{intro}{Color.Reset}')
        print(f'rpmlint: {__version__}')
        print('configuration:')
        for config in self.config.conf_files:
            print(f'    {config}')
        if self.options['rpmlintrc']:
            rpmlintrc = self.options['rpmlintrc']
            print(f'rpmlintrc: {rpmlintrc}')
        no_checks = len(self.config.configuration['Checks'])
        no_pkgs = len(self.options['installed']) + len(self.options['rpmfile'])
        print(f'{Color.Bold}checks: {no_checks}, packages: {no_pkgs}{Color.Reset}')
        print('')

    def validate_installed_packages(self, packages):
        for pkg in packages:
            self.run_checks(pkg)

    def validate_files(self, files):
        """
        Run all the check for passed file list
        """
        if not files:
            if self.packages_checked == 0:
                # print warning only if we didn't process even installed files
                print_warning('There are no files to process nor additional arguments.')
                print_warning('Nothing to do, aborting.')
            return
        # check all elements if they are a folder or a file with proper suffix
        # and expand everything
        packages = self._expand_filelist(files)
        for pkg in packages:
            self.validate_file(pkg)

    def _expand_filelist(self, files):
        packages = []
        for pkg in files:
            if pkg.is_file() and self._check_valid_suffix(pkg):
                packages.append(pkg)
            elif pkg.is_dir():
                packages.extend(self._expand_filelist(pkg.iterdir()))
        return packages

    @staticmethod
    def _check_valid_suffix(filename):
        if any(ext == filename.suffix for ext in ['.rpm', '.spm', '.spec']):
            return True
        return False

    def validate_file(self, pname):
        try:
            if pname.suffix == '.rpm' or pname.suffix == '.spm':
                with Pkg(pname, self.config.configuration['ExtractDir'],
                         verbose=self.config.info) as pkg:
                    self.run_checks(pkg)
            elif pname.suffix == '.spec':
                with FakePkg(pname) as pkg:
                    self.run_checks(pkg)
        except Exception as e:
            print_warning(f'(none): E: fatal error while reading {pname}: {e}')
            sys.exit(3)

    def run_checks(self, pkg):
        spec_checks = isinstance(pkg, FakePkg)
        for checker in self.checks:
            if checker not in self.check_duration:
                self.check_duration[checker] = 0
            start = time.monotonic()
            fn = self.checks[checker].check_spec if spec_checks else self.checks[checker].check
            fn(pkg)
            self.check_duration[checker] += time.monotonic() - start

        if spec_checks:
            self.specfiles_checked += 1
        else:
            self.packages_checked += 1

    def print_config(self):
        """
        Just output the current configuration
        """
        self.config.print_config()

    def print_explanation(self, messages, config):
        """
        Print out detailed explanation for the specified messages
        """
        for message in messages:
            explanation = self.output.get_description(message, config)
            if not explanation:
                explanation = 'Unknown message, please report a bug if the description should be present.\n\n'
            print(f'{message}:\n{explanation}')

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
