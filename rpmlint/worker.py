"""
Run rpmlint checks on a single package in a worker process.

Each worker process builds its check instances once via init_worker()
and reuses them for every package it handles. Workers never print or
filter anything directly; anything checks print is captured and
returned with the structured results so the main process can replay
it in deterministic order. Parallel execution therefore cannot tangle
the output.
"""

import contextlib
import importlib
import io
from pathlib import Path
import time
import traceback

from rpmlint.filter import ResultCollector
from rpmlint.pkg import FakePkg, get_installed_pkgs, Pkg

# Per-worker state installed by init_worker(): (config, extract_dir,
# checks, init_collector). The check instances are reused across all
# packages the worker handles; a fresh ResultCollector is attached to
# them for every package.
_worker_state = None


def init_worker(config, check_names, extract_dir):
    """
    Build the check instances once per worker process.

    Called once in each worker (or once in-process for jobs=1) before
    any package is checked, so module imports, config parsing and check
    construction are not repeated for every package.
    """
    global _worker_state
    checks = {}
    # Collects anything checks register at construction time (e.g.
    # issue descriptions); merged into every result below.
    init_collector = ResultCollector()
    for name in check_names:
        module = importlib.import_module(f'rpmlint.checks.{name}')
        checks[name] = getattr(module, name)(config, init_collector)
    _worker_state = (config, extract_dir, checks, init_collector)


def check_package(task):
    """
    Check a single package and return the structured results.

    Args:
        task: (kind, ident) where kind is 'file' (ident is a path
            string) or 'installed' (ident is a (name, index) pair for
            get_installed_pkgs()). The worker must have been set up
            with init_worker() first.

    Returns:
        dict with issues, error_details, durations, timers,
        checked_files, after_states, pkg_name, pkg_arch, is_spec,
        captured stdout/stderr and fatal (a traceback string if the
        package could not be checked).
    """
    kind, ident = task
    config, extract_dir, checks, init_collector = _worker_state
    # every package gets a fresh collector while the check instances
    # are reused
    collector = ResultCollector()
    for checker in checks.values():
        checker.output = collector
    files_before = {name: checker.checked_files or 0 for name, checker in checks.items()}

    result = {
        'issues': [],
        'error_details': {},
        'durations': {},
        'timers': {},
        'checked_files': {},
        'after_states': {},
        'pkg_name': str(ident) if kind == 'file' else ident[0],
        'pkg_arch': None,
        'is_spec': False,
        'fatal': None,
        'stdout': '',
        'stderr': '',
    }

    # Checks may print directly (e.g. print_warning); capture it so the
    # main process can replay it in deterministic order instead of
    # letting workers tangle the output.
    stdout_buf = io.StringIO()
    stderr_buf = io.StringIO()
    with contextlib.redirect_stdout(stdout_buf), contextlib.redirect_stderr(stderr_buf):
        _check_package_body(kind, ident, config, extract_dir, checks,
                            collector, files_before, result)
    result['stdout'] = stdout_buf.getvalue()
    result['stderr'] = stderr_buf.getvalue()
    result['issues'] = collector.issues
    # descriptions registered at construction time are static per check
    error_details = dict(init_collector.error_details)
    error_details.update(collector.error_details)
    result['error_details'] = error_details
    return result


def _check_package_body(kind, ident, config, extract_dir, checks,
                        collector, files_before, result):
    """Load the package and run all checks, filling in result."""
    try:
        if kind == 'file':
            path = Path(ident)
            if path.suffix == '.spec':
                pkg = FakePkg(path)
                result['is_spec'] = True
            else:
                pkg = Pkg(path, extract_dir, verbose=config.info)
        else:
            pkg = get_installed_pkgs(ident[0])[ident[1]]
    except Exception:
        result['fatal'] = traceback.format_exc()
        return

    # installed packages are not used as context managers, mirroring
    # Lint.validate_installed_packages
    context = pkg if kind == 'file' else contextlib.nullcontext(pkg)
    try:
        with context:
            result['pkg_arch'] = pkg.arch
            if kind == 'file' and not result['is_spec']:
                result['timers'] = dict(pkg.timers)
            spec_checks = isinstance(pkg, FakePkg)
            for name, checker in checks.items():
                start = time.monotonic()
                if spec_checks:
                    checker.check_spec(pkg)
                else:
                    checker.check(pkg)
                result['durations'][name] = time.monotonic() - start
                files_now = checker.checked_files or 0
                if files_now > files_before[name]:
                    result['checked_files'][name] = files_now - files_before[name]
                # export_state() also clears the exported state, so each
                # result only carries this package's contribution
                state = checker.export_state()
                if state is not None:
                    result['after_states'][name] = state
    except Exception:
        result['fatal'] = traceback.format_exc()
        # drop state accumulated before the failure so a package that
        # could not be checked never contributes to after_checks()
        for checker in checks.values():
            checker.export_state()
    # restore per-package check state for the next package, mirroring
    # the reset_checks() call the sequential runner made after every
    # package
    for checker in checks.values():
        checker.reset()
