"""
Run rpmlint checks on a single package in a worker process.

Workers never print or filter anything; they return structured results
that the main process replays through Filter in deterministic order,
so parallel execution cannot tangle the output.
"""

import contextlib
import importlib
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
        checked_files, after_states, pkg_name, pkg_arch, is_spec and
        fatal (a traceback string if the package could not be loaded).
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
    }

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
        return result

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

    result['issues'] = collector.issues
    result['error_details'] = collector.error_details
    return result
