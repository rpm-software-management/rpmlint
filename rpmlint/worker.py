"""
Run rpmlint checks on a single package in a worker process.

Workers never print or filter anything directly; anything checks print
is captured and returned with the structured results so the main
process can replay it in deterministic order. Parallel execution
therefore cannot tangle the output.
"""

import contextlib
import importlib
import io
from pathlib import Path
import time
import traceback

from rpmlint.filter import ResultCollector
from rpmlint.pkg import FakePkg, get_installed_pkgs, Pkg


def check_package(task):
    """
    Check a single package and return the structured results.

    Args:
        task: (kind, ident, config, check_names, extract_dir) where kind
            is 'file' (ident is a path string) or 'installed' (ident is
            a (name, index) pair for get_installed_pkgs()).

    Returns:
        dict with issues, error_details, durations, timers,
        checked_files, after_states, pkg_name, pkg_arch, is_spec,
        captured stdout/stderr and fatal (a traceback string if the
        package could not be checked).
    """
    kind, ident, config, check_names, extract_dir = task
    collector = ResultCollector()
    checks = {}
    for name in check_names:
        module = importlib.import_module(f'rpmlint.checks.{name}')
        checks[name] = getattr(module, name)(config, collector)

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
        _check_package_body(kind, ident, config, extract_dir,
                            collector, checks, result)
    result['stdout'] = stdout_buf.getvalue()
    result['stderr'] = stderr_buf.getvalue()
    result['issues'] = collector.issues
    result['error_details'] = collector.error_details
    return result


def _check_package_body(kind, ident, config, extract_dir,
                        collector, checks, result):
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
                if checker.checked_files:
                    result['checked_files'][name] = checker.checked_files
                state = checker.export_state()
                if state is not None:
                    result['after_states'][name] = state
    except Exception:
        result['fatal'] = traceback.format_exc()
