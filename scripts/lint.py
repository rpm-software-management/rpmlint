#!/usr/bin/python -ttOu
# -*- coding: utf-8 -*-
#############################################################################
# File          : rpmlint
# Package       : rpmlint
# Author        : Frederic Lepied
# Created on    : Mon Sep 27 19:20:18 1999
# Purpose       : main entry point: process options, load the checks and run
#                 the checks.
#############################################################################

import getopt
import glob
import locale
import os
import re
import stat
import sys
import tempfile

try:
    import importlib
except ImportError:  # Python < 2.7
    importlib = None
    import imp

# Do not import anything that initializes its global variables from
# Config at load time here (or anything that imports such a thing),
# that results in those variables initialized before config files are
# loaded which is too early - settings from config files won't take
# place for those variables.

import rpmlint.AbstractCheck
import rpmlint.Config as Config
import rpmlint.Pkg as Pkg
from rpmlint.Filter import badnessScore, badnessThreshold, printAllReasons, \
    printDescriptions, printed_messages, printInfo, setRawOut


_default_user_conf = '%s/rpmlint' % \
    (os.environ.get('XDG_CONFIG_HOME') or '~/.config')


# Print usage information
def usage(name):
    print('''usage: %s [<options>] <rpm files|installed packages|specfiles|dirs>
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
\t[   --rawout <file>]
\t[-f|--file <user config file to use instead of %s]
\t[-o|--option <key value>]'''
          % (name, _default_user_conf))


# Print version information
def printVersion():
    print('rpmlint version %s' % Config.__version__)


def loadCheck(name):
    '''Load a (check) module by its name, unless it is already loaded.'''
    # Avoid loading more than once (initialization costs)
    loaded = sys.modules.get(name)
    if loaded:
        return loaded
    if importlib:
        try:
            importlib.import_module('.%s' % name, package='rpmlint')
        except ImportError:
            importlib.import_module(name)
    else:
        (fobj, pathname, description) = imp.find_module(name)
        with fobj:
            imp.load_module(name, fobj, pathname, description)


#############################################################################
# main program
#############################################################################
def main():

    locale.setlocale(locale.LC_COLLATE, '')

    # Add check dirs to the front of load path
    sys.path[0:0] = Config.checkDirs()

    # Load all checks
    for c in Config.allChecks():
        loadCheck(c)

    packages_checked = 0
    specfiles_checked = 0

    try:
        # Loop over all file names given in arguments
        dirs = []
        for arg in args:
            pkgs = []
            isfile = False
            try:
                if arg == "-":
                    arg = "(standard input)"
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
                        if arg.endswith(".spec"):
                            # Short-circuit spec file checks
                            with Pkg.FakePkg(arg) as pkg:
                                runSpecChecks(pkg, arg)
                            specfiles_checked += 1
                        elif "/" in arg or arg.endswith(".rpm") or \
                                arg.endswith(".spm"):
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
                        Pkg.warn(
                            '(none): E: no installed packages by name %s' % arg)
                    else:
                        ipkgs.sort(key=lambda x: locale.strxfrm(
                            x.header.sprintf("%{NAME}.%{ARCH}")))
                        pkgs.extend(ipkgs)
            except KeyboardInterrupt:
                if isfile:
                    arg = os.path.abspath(arg)
                Pkg.warn(
                    '(none): E: interrupted, exiting while reading %s' % arg)
                sys.exit(2)
            except Exception as e:
                if isfile:
                    arg = os.path.abspath(arg)
                Pkg.warn('(none): E: error while reading %s: %s' % (arg, e))
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
                            Pkg.warn(
                                '(none): E: interrupted while reading %s' %
                                fname)
                            sys.exit(2)
                        except Exception as e:
                            Pkg.warn(
                                '(none): E: while reading %s: %s' % (fname, e))
                            continue
            except Exception as e:
                Pkg.warn(
                    '(none): E: error while reading dir %s: %s' % (dname, e))
                continue

        if printAllReasons():
            Pkg.warn('(none): E: badness %d exceeds threshold %d, aborting.' %
                     (badnessScore(), badnessThreshold()))
            sys.exit(66)

    finally:
        print("%d packages and %d specfiles checked; %d errors, %d warnings."
              % (packages_checked, specfiles_checked,
                 printed_messages["E"], printed_messages["W"]))

    if printed_messages["E"] > 0:
        sys.exit(64)
    sys.exit(0)


def runChecks(pkg):

    if verbose:
        printInfo(pkg, 'checking')

    for name in Config.allChecks():
        check = AbstractCheck.AbstractCheck.known_checks.get(name)
        if check:
            check.verbose = verbose
            check.check(pkg)
        else:
            Pkg.warn('(none): W: unknown check %s, skipping' % name)


def runSpecChecks(pkg, fname, spec_lines=None):

    if verbose:
        printInfo(pkg, 'checking')

    for name in Config.allChecks():
        check = AbstractCheck.AbstractCheck.known_checks.get(name)
        if check:
            check.verbose = verbose
            check.check_spec(pkg, fname, spec_lines)
        else:
            Pkg.warn('(none): W: unknown check %s, skipping' % name)


#############################################################################
#
#############################################################################

argv0 = os.path.basename(sys.argv[0])

# parse options
try:
    (opt, args) = getopt.getopt(
        sys.argv[1:], 'iI:c:C:hVvanE:f:o:',
        ['info', 'explain=', 'check=', 'checkdir=', 'help', 'version',
         'verbose', 'all', 'noexception', 'extractdir=', 'file=', 'option=',
         'rawout='])
except getopt.GetoptError as e:
    Pkg.warn("%s: %s" % (argv0, e))
    usage(argv0)
    sys.exit(1)

# process options
checkdir = '/usr/share/rpmlint'
checks = []
verbose = False
extract_dir = None
conf_file = _default_user_conf
info_error = set()

# load global config files
configs = glob.glob('/etc/rpmlint/*config')
configs.sort()

# Was rpmlint invoked as a prefixed variant?
m = re.match(r"(?P<prefix>[\w-]+)-rpmlint(\.py)?", argv0)
if m:
    # Okay, we're a prefixed variant. Look for the variant config.
    # If we find it, use it. If not, fallback to the default.
    prefix = m.group('prefix')
    if os.path.isfile('/usr/share/rpmlint/config.%s' % prefix):
        configs.insert(0, '/usr/share/rpmlint/config.%s' % prefix)
    else:
        configs.insert(0, '/usr/share/rpmlint/config')
else:
    configs.insert(0, '/usr/share/rpmlint/config')

for f in configs:
    try:
        with open(f) as fobj:
            exec(compile(fobj.read(), f, 'exec'))
    except IOError:
        pass
    except Exception as e:
        Pkg.warn('(none): W: error loading %s, skipping: %s' % (f, e))
# pychecker fix
del f

config_overrides = {}

# process command line options
for o in opt:
    if o[0] in ('-c', '--check'):
        checks.append(o[1])
    elif o[0] in ('-i', '--info'):
        Config.info = True
    elif o[0] in ('-I', '--explain'):
        # split by comma for deprecated backwards compatibility with < 1.2
        info_error.update(o[1].split(','))
    elif o[0] in ('-h', '--help'):
        usage(argv0)
        sys.exit(0)
    elif o[0] in ('-C', '--checkdir'):
        Config.addCheckDir(o[1])
    elif o[0] in ('-v', '--verbose'):
        verbose = True
    elif o[0] in ('-V', '--version'):
        printVersion()
        sys.exit(0)
    elif o[0] in ('-E', '--extractdir'):
        extract_dir = o[1]
        Config.setOption('ExtractDir', extract_dir)
    elif o[0] in ('-n', '--noexception'):
        Config.no_exception = True
    elif o[0] in ('-a', '--all'):
        if '*' not in args:
            args.append('*')
    elif o[0] in ('-f', '--file'):
        conf_file = o[1]
    elif o[0] in ('-o', '--option'):
        kv = o[1].split(None, 1)
        if len(kv) == 1:
            config_overrides[kv[0]] = None
        else:
            config_overrides[kv[0]] = eval(kv[1])
    elif o[0] in ('--rawout',):
        setRawOut(o[1])

# load user config file
try:
    expconf = os.path.expanduser(conf_file)
    with open(expconf) as fobj:
        exec(compile(fobj.read(), expconf, 'exec'))
except IOError:
    pass
except Exception as e:
    Pkg.warn('(none): W: error loading %s, skipping: %s' % (conf_file, e))

# apply config overrides
for key, value in config_overrides.items():
    Config.setOption(key, value)

if not extract_dir:
    extract_dir = Config.getOption('ExtractDir', tempfile.gettempdir())

if info_error:
    Config.info = True
    sys.path[0:0] = Config.checkDirs()
    for c in checks:
        Config.addCheck(c)
    for c in Config.allChecks():
        loadCheck(c)
    for e in sorted(info_error):
        print("%s:" % e)
        printDescriptions(e)
    sys.exit(0)

# if no argument print usage
if not args:
    usage(argv0)
    sys.exit(1)

if __name__ == '__main__':
    if checks:
        Config.resetChecks()
        for check in checks:
            Config.addCheck(check)
    main()

# rpmlint ends here
