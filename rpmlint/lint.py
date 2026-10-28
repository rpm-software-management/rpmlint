from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor
import importlib
import operator
import sys
from tempfile import gettempdir
import time
from types import SimpleNamespace

from rpmlint import worker
from rpmlint.color import Color
from rpmlint.config import Config
from rpmlint.filter import Filter
from rpmlint.helpers import print_warning, string_center
from rpmlint.pkg import get_installed_pkgs
from rpmlint.version import __version__


class Lint:
    """
    Generic object handling the basic rpmlint operations
    """

    def __init__(self, options):
        # initialize configuration
        self.checks = {}
        self.options = options
        self.packages_checked = 0
        self.specfiles_checked = 0
        # set when any package hit a fatal error; the run continues but
        # still fails with exit code 3 at the end
        self.had_fatal_error = False
        self.check_duration = defaultdict(int)
        if options['config']:
            self.config = Config(options['config'])
        else:
            self.config = Config()

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
        # last processed package (stub), used for validate_filters()
        self._last_pkg = None
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

        # check installed packages first and then files; after_checks()
        # runs once per batch so post checks see a consistent state
        if self.options['installed']:
            self._check_packages(self._installed_tasks(self.options['installed']),
                                 run_after_checks=not self.options['rpmfile'])
        self._check_packages(self._file_tasks(self.options['rpmfile']),
                             run_after_checks=True)
        if not self.options['ignore_unused_rpmlintrc'] and self._last_pkg is not None:
            self.output.validate_filters(self._last_pkg)
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
            all_promoted = self.output.printed_messages['E'] == self.output.promoted_to_error
            retcode = 65 if all_promoted else 64

        if self.had_fatal_error:
            # a fatal error fails the run, but only after everything
            # else has been processed and reported
            retcode = 3

        self._maybe_print_reports()

        duration = time.monotonic() - start
        error_messages = self.output.printed_messages['E']
        warning_messages = self.output.printed_messages['W']
        msg = string_center(f'{self.packages_checked} packages and {self.specfiles_checked} specfiles checked; '
                            f'{error_messages} errors, {warning_messages} warnings'
                            f', {self.output.filtered_out} filtered, '
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

    def _get_color_time_report_value(self, fraction):
        if fraction > 25:
            color = Color.Red
        elif fraction > 5:
            color = Color.Yellow
        else:
            color = ''
        return f'{color}{fraction:17.1f}{Color.Reset}'

    def _print_time_report(self):
        PERCENT_THRESHOLD = 1
        TIME_THRESHOLD = 0.1
        total = sum(self.check_duration.values())
        checked_files = [check.checked_files for check in self.checks.values() if check.checked_files]
        total_checked_files = max(checked_files) if checked_files else ''
        print(f'{Color.Bold}Check time report{Color.Reset} (>{PERCENT_THRESHOLD}% & >{TIME_THRESHOLD}s):')

        check = format('Check', '32s')
        duration = format('Duration (in s)', '>12')
        fraction = format('Fraction (in %)', '>17')
        print(f'{Color.Bold}    {check} {duration} {fraction}  Checked files{Color.Reset}')

        for check, duration in sorted(self.check_duration.items(), key=operator.itemgetter(1), reverse=True):
            fraction = 100.0 * duration / total
            if fraction < PERCENT_THRESHOLD or duration < TIME_THRESHOLD:
                continue

            checked_files = ''
            if check in self.checks:
                checked = self.checks[check].checked_files
                if checked:
                    checked_files = checked
            print(f'    {check:32s} {duration:15.1f} {self._get_color_time_report_value(fraction)} {checked_files:>14}')

        print(f'    {"TOTAL":32s} {total:15.1f} {100:17.1f} {total_checked_files:>14}\n')       # noqa Q000

    def _installed_tasks(self, packages):
        """
        Build worker tasks for installed packages, warning about unknown names.
        """
        tasks = []
        for name in packages:
            pkgs = get_installed_pkgs(name)
            if pkgs:
                tasks.extend(('installed', (name, index)) for index in range(len(pkgs)))
            else:
                print_warning(f'(none): E: there is no installed rpm "{name}".')
        return tasks

    def _file_tasks(self, files):
        """
        Build worker tasks for the passed file list, expanding directories
        and sorting so the output is stable.
        """
        if not files:
            if self.packages_checked == 0:
                # print warning only if we didn't process even installed files
                print_warning('There are no files to process nor additional arguments.')
                print_warning('Nothing to do, aborting.')
            return []
        # check all elements if they are a folder or a file with proper suffix
        # and expand everything
        packages = sorted(self._expand_filelist(files))
        return [('file', str(pkg)) for pkg in packages]

    def _check_packages(self, tasks, run_after_checks):
        """
        Check packages, optionally in parallel worker processes, and replay
        their results through the filter in deterministic order.
        """
        if not tasks:
            return
        check_names = list(self.checks.keys())
        extract_dir = self.config.configuration['ExtractDir']
        jobs = max(1, self.options['jobs'])
        idents = [(kind, ident) for kind, ident in tasks]
        if jobs == 1:
            # in-process execution, easier to debug
            worker.init_worker(self.config, check_names, extract_dir)
            results = [worker.check_package(task) for task in idents]
        else:
            # the initializer builds the check instances once per
            # worker instead of once per package
            with ProcessPoolExecutor(max_workers=jobs,
                                     initializer=worker.init_worker,
                                     initargs=(self.config, check_names, extract_dir)) as executor:
                results = list(executor.map(worker.check_package, idents))
        for (kind, ident), result in zip(tasks, results):
            display = ident[0] if kind == 'installed' else ident
            self._replay_result(display, result)
        if run_after_checks:
            for checker in self.checks.values():
                checker.after_checks()
        # drop the merged cross-package state so batches stay independent
        self.reset_checks()

    def _replay_result(self, ident, result):
        """
        Feed one worker result through the filter, preserving the order
        in which the packages were passed on the command line.
        """
        # Replay anything the checks printed directly (e.g. warnings
        # about missing optional dependencies) before the buffered
        # issue output, matching sequential execution.
        sys.stdout.write(result['stdout'])
        sys.stderr.write(result['stderr'])
        if result['fatal'] is not None:
            print_warning(f'(none): E: fatal error while reading {ident}: {result["fatal"]}')
            # Record the fatal error and continue with the remaining
            # packages; the exit code is set at the end once everything
            # has been reported.
            self.had_fatal_error = True
        for level, name, arch, linenum, issue, details in result['issues']:
            pkg = SimpleNamespace(name=name, arch=arch, current_linenum=linenum)
            self.output.add_info(level, pkg, issue, *details)
        self.output.error_details.update(result['error_details'])
        for check_name, state in result['after_states'].items():
            self.checks[check_name].import_state(state)
        for check_name, duration in result['durations'].items():
            self.check_duration[check_name] += duration
        for check_name, count in result['checked_files'].items():
            checker = self.checks[check_name]
            checker.checked_files = (checker.checked_files or 0) + count
        for timer, duration in result['timers'].items():
            self.check_duration[timer] += duration
        if result['is_spec']:
            self.specfiles_checked += 1
        else:
            self.packages_checked += 1
        self._last_pkg = SimpleNamespace(name=result['pkg_name'], arch=result['pkg_arch'],
                                         current_linenum=None)

    def _load_rpmlintrc(self):
        """
        Load rpmlintrc from argument or load up from folder
        """
        if self.options['rpmlintrc']:
            for rcfile in self.options['rpmlintrc']:
                self.config.load_rpmlintrc(rcfile)
        else:
            # load only from the same folder specname.rpmlintrc or specname-rpmlintrc
            # do this only in a case where there is one folder parameter or one file
            # to avoid multiple folders handling
            rpmlintrc = []
            if len(self.options['rpmfile']) != 1:
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

    def _expand_filelist(self, files):
        packages = []
        for pkg in files:
            if pkg.is_file() and pkg.suffix in ('.rpm', '.spm', '.spec'):
                packages.append(pkg)
            elif pkg.is_dir():
                packages.extend(self._expand_filelist(pkg.iterdir()))
        return packages

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
                # check if it's a WarnOnFunction warning configuration
                forbidden_functions = config.configuration['WarnOnFunction']
                if message in forbidden_functions:
                    explanation = forbidden_functions[message].get('description')

            if not explanation:
                explanation = 'Unknown message, please report a bug if the description should be present.\n\n'

            print(f'{message}:\n{explanation}')

    def load_checks(self):
        """
        Load all checks based on the config, skipping those already loaded
        SingletonTM
        """

        selected_checks = self.options['checks']
        if selected_checks:
            selected_checks = selected_checks.split(',')

        for check in self.config.configuration['Checks']:
            if check in self.checks:
                continue
            if not selected_checks or check in selected_checks:
                self.checks[check] = self.load_check(check)

    def reset_checks(self):
        """
        Reset all check objects to set to the default state
        """
        for check in self.checks.values():
            check.reset()

    def load_check(self, name):
        """Load a (check) module by its name, unless it is already loaded."""
        module = importlib.import_module(f'.{name}', package='rpmlint.checks')
        klass = getattr(module, name)
        obj = klass(self.config, self.output)
        return obj
