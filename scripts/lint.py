#!/usr/bin/python3
#############################################################################
# File          : rpmlint
# Package       : rpmlint
# Author        : Frederic Lepied
# Created on    : Mon Sep 27 19:20:18 1999
# Purpose       : main entry point: process options, load the checks and run
#                 the checks.
#############################################################################

import contextlib
import getopt
import importlib
import locale
import os
import stat
import sys
import tempfile

# Do not import anything that initializes its global variables from
# Config at load time here (or anything that imports such a thing),
# that results in those variables initialized before config files are
# loaded which is too early - settings from config files won't take
# place for those variables.

from rpmlint.version import __version__
from rpmlint import pkg as Pkg
from rpmlint.checks.AbstractCheck import AbstractCheck
from rpmlint.config import Config
from rpmlint.filter import Filter
from rpmlint.helpers import print_warning


# Print usage information
def usage(name):
    print("""usage: %s [<options>] <rpm files|installed packages|specfiles|dirs>
  options:
\t[-i|--info]
\t[-I|--explain <messageid>]
\t[-c|--check <check>]
\t[-a|--all]
\t[-C|--checkdir <checkdir>]
\t[-h|--help]
\t[-v|--verbose]
\t[-E|--extractdir <dir>]
\t[-V|--version]
\t[-n|--noexception]
\t[-f|--file <user config file to use>]
\t[-o|--option <key value>]"""
          % (name))


# Print version information
def printVersion():
    print('rpmlint version %s' % __version__)


def loadCheck(name, config, output):
    """Load a (check) module by its name, unless it is already loaded."""
    # Avoid loading more than once (initialization costs)
    loaded = sys.modules.get(name)
    if loaded:
        return
    module = importlib.import_module('.{}'.format(name), package='rpmlint.checks')
    klass = getattr(module, name)
    obj = klass(config, output)
    return obj


#############################################################################
# main program
#############################################################################
def main():

    # we'll try to sort with locale settings, but we don't fail if not possible
    with contextlib.suppress(locale.Error):
        locale.setlocale(locale.LC_COLLATE, '')

    output = Filter(cfg)

    # Load all checks
    for c in cfg.configuration['Checks']:
        loadCheck(c, cfg, output)

    packages_checked = 0
    specfiles_checked = 0

    try:
        # Loop over all file names given in arguments
        dirs = []
        for arg in args:
            pkgs = []
            isfile = False
            try:
                if arg == '-':
                    arg = '(standard input)'
                    # Short-circuit stdin spec file check
                    stdin = sys.stdin.readlines()
                    if not stdin:
                        continue
                    with Pkg.FakePkg(arg) as pkg:
                        runSpecChecks(pkg, None, spec_lines=stdin)
                    specfiles_checked += 1
                    continue

                try:
                    st = os.stat(arg)
                    isfile = True
                    if stat.S_ISREG(st[stat.ST_MODE]):
                        if arg.endswith('.spec'):
                            # Short-circuit spec file checks
                            with Pkg.FakePkg(arg) as pkg:
                                runSpecChecks(pkg, arg)
                            specfiles_checked += 1
                        elif '/' in arg or arg.endswith('.rpm') or \
                                arg.endswith('.spm'):
                            pkgs.append(Pkg.Pkg(arg, extract_dir))
                        else:
                            raise OSError

                    elif stat.S_ISDIR(st[stat.ST_MODE]):
                        dirs.append(arg)
                        continue
                    else:
                        raise OSError
                except OSError:
                    ipkgs = Pkg.getInstalledPkgs(arg)
                    if not ipkgs:
                        print_warning(
                            '(none): E: no installed packages by name %s' % arg)
                    else:
                        ipkgs.sort(key=lambda x: locale.strxfrm(
                            x.header.sprintf('%{NAME}.%{ARCH}')))
                        pkgs.extend(ipkgs)
            except KeyboardInterrupt:
                if isfile:
                    arg = os.path.abspath(arg)
                print_warning(
                    '(none): E: interrupted, exiting while reading %s' % arg)
                sys.exit(2)
            except Exception as e:
                if isfile:
                    arg = os.path.abspath(arg)
                print_warning('(none): E: error while reading %s: %s' % (arg, e))
                pkgs = []
                continue

            for pkg in pkgs:
                with pkg:
                    runChecks(pkg)
                packages_checked += 1

        for dname in dirs:
            try:
                for path, _, files in os.walk(dname):
                    for fname in files:
                        fname = os.path.abspath(os.path.join(path, fname))
                        try:
                            if fname.endswith('.rpm') or \
                               fname.endswith('.spm'):
                                with Pkg.Pkg(fname, extract_dir) as pkg:
                                    runChecks(pkg)
                                packages_checked += 1

                            elif fname.endswith('.spec'):
                                with Pkg.FakePkg(fname) as pkg:
                                    runSpecChecks(pkg, fname)
                                specfiles_checked += 1

                        except KeyboardInterrupt:
                            print_warning(
                                '(none): E: interrupted while reading %s' %
                                fname)
                            sys.exit(2)
                        except Exception as e:
                            print_warning(
                                '(none): E: while reading %s: %s' % (fname, e))
                            continue
            except Exception as e:
                print_warning(
                    '(none): E: error while reading dir %s: %s' % (dname, e))
                continue

        print(output.print_results(output.results))

        if output.badness_threshold > 0 and output.score > output.badness_threshold:
            print_warning('(none): E: badness %d exceeds threshold %d, aborting.' %
                          (output.score, output.badness_threshold))
            sys.exit(66)

    finally:
        print('%d packages and %d specfiles checked; %d errors, %d warnings.'
              % (packages_checked, specfiles_checked,
                 output.printed_messages['E'], output.printed_messages['W']))

    if output.printed_messages['E'] > 0:
        sys.exit(64)
    sys.exit(0)


def runChecks(pkg):
    for name in cfg.configuration['Checks']:
        check = AbstractCheck.known_checks.get(name)
        if check:
            check.verbose = verbose
            check.check(pkg)
        else:
            print_warning('(none): W: unknown check %s, skipping' % name)


def runSpecChecks(pkg, fname, spec_lines=None):
    for name in cfg.configuration['Checks']:
        check = AbstractCheck.known_checks.get(name)
        if check:
            check.verbose = verbose
            check.check_spec(pkg, fname, spec_lines)
        else:
            print_warning('(none): W: unknown check %s, skipping' % name)


#############################################################################
#
#############################################################################

argv0 = os.path.basename(sys.argv[0])

# parse options
try:
    (opt, args) = getopt.getopt(
        sys.argv[1:], 'iI:c:C:hVvanE:f:o:',
        ['info', 'explain=', 'check=', 'help', 'version',
         'verbose', 'all', 'noexception', 'extractdir=', 'file=', 'option=',
         ])
except getopt.GetoptError as e:
    print_warning('%s: %s' % (argv0, e))
    usage(argv0)
    sys.exit(1)

# process options
checks = []
verbose = False
extract_dir = None
info_error = set()

config_overrides = {}

# load global config files
cfg = Config()
extract_dir = cfg.configuration['ExtractDir']

# process command line options
for o in opt:
    if o[0] in ('-c', '--check'):
        checks.append(o[1])
    elif o[0] in ('-i', '--info'):
        cfg.info = True
    elif o[0] in ('-I', '--explain'):
        # split by comma for deprecated backwards compatibility with < 1.2
        info_error.update(o[1].split(','))
    elif o[0] in ('-h', '--help'):
        usage(argv0)
        sys.exit(0)
    elif o[0] in ('-v', '--verbose'):
        verbose = True
    elif o[0] in ('-V', '--version'):
        printVersion()
        sys.exit(0)
    elif o[0] in ('-E', '--extractdir'):
        extract_dir = o[1]
        cfg.configuration['ExtractDir'] = extract_dir
    elif o[0] in ('-n', '--noexception'):
        cfg.no_exception = True
    elif o[0] in ('-a', '--all'):
        if '*' not in args:
            args.append('*')
    elif o[0] in ('-f', '--file'):
        cfg.load_config(o[1])
    elif o[0] in ('-o', '--option'):
        kv = o[1].split(None, 1)
        if len(kv) == 1:
            config_overrides[kv[0]] = None
        else:
            config_overrides[kv[0]] = eval(kv[1])

# apply config overrides
for key, value in config_overrides.items():
    cfg.configuration[key] = value

if not extract_dir:
    extract_dir = tempfile.gettempdir()

if info_error:
    cfg.info = True
    output = Filter(cfg)
    for c in checks:
        cfg.add_check(c)
    for c in cfg.configuration['Checks']:
        loadCheck(c, cfg, output)
    for e in sorted(info_error):
        print('{}:'.format(e))
        print(output.get_description(e))
    sys.exit(0)

# if no argument print usage
if not args:
    usage(argv0)
    sys.exit(1)

if __name__ == '__main__':
    if checks:
        cfg.reset_checks()
        for check in checks:
            cfg.add_check(check)
    main()

# rpmlint ends here
