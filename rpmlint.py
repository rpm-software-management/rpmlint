# -*- coding: utf-8 -*-
#############################################################################
# File          : rpmlint.py
# Package       : rpmlint
# Author        : Frederic Lepied
# Created on    : Mon Sep 27 19:20:18 1999
# Version       : $Id$
# Purpose       : main entry point: process options, load the checks and run
#                 the checks.
#############################################################################

import getopt
import glob
import imp
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

from Filter import badnessScore, badnessThreshold, printAllReasons, \
     printDescriptions, printInfo, printed_messages
import AbstractCheck
import Config
import Pkg


version = '@VERSION@'

_default_user_conf = '%s/rpmlint' % \
    (os.environ.get('XDG_CONFIG_HOME') or '~/.config')

# Print usage information
def usage(name):
    print '''usage: %s [<options>] <rpm files|installed packages|specfiles|dirs>
  options:
\t[-i|--info]
\t[-I <error,error,...>]
\t[-c|--check <check>]
\t[-a|--all]
\t[-C|--checkdir <checkdir>]
\t[-h|--help]
\t[-v|--verbose]
\t[-E|--extractdir <dir>]
\t[-V|--version]
\t[-n|--noexception]
\t[-f|--file <user config file to use instead of %s]''' \
        % (name, _default_user_conf)

# Print version information
def printVersion():
    print 'rpmlint version', version, 'Copyright (C) 1999-2007 Frederic Lepied, Mandriva'

def loadCheck(name):
    '''Load a (check) module by its name, unless it is already loaded.'''
    # Avoid loading more than once (initialization costs)
    loaded = sys.modules.get(name)
    if loaded:
        return loaded 
    (fobj, pathname, description) = imp.find_module(name)
    try:
        imp.load_module(name, fobj, pathname, description)
    finally:
        fobj.close()

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
    do_spec_check = 'SpecCheck' in Config.allChecks()
    if do_spec_check:
        # See comments in "top level import section" for why this isn't
        # imported earlier.
        import SpecCheck

    try:
        # Loop over all file names given in arguments
        dirs = []
        for arg in args:
            pkgs = []
            isfile = False
            try:
                try:
                    st = os.stat(arg)
                    isfile = True
                    if stat.S_ISREG(st[stat.ST_MODE]):
                        if not arg.endswith(".spec"):
                            pkgs.append(Pkg.Pkg(arg, extract_dir))
                        elif do_spec_check:
                            # Short-circuit spec file checks
                            pkg = Pkg.FakePkg(arg)
                            check = SpecCheck.SpecCheck()
                            check.check_spec(pkg, arg)
                            pkg.cleanup()
                            specfiles_checked += 1

                    elif stat.S_ISDIR(st[stat.ST_MODE]):
                        dirs.append(arg)
                        continue
                    else:
                        raise OSError
                except OSError:
                    ipkgs = Pkg.getInstalledPkgs(arg)
                    if not ipkgs:
                        sys.stderr.write(
                            '(none): E: no installed packages by name %s\n'
                            % arg)
                    else:
                        ipkgs.sort(key = lambda x: locale.strxfrm(
                                x.header.sprintf("%{NAME}.%{ARCH}")))
                        pkgs.extend(ipkgs)
            except KeyboardInterrupt:
                if isfile:
                    arg = os.path.abspath(arg)
                sys.stderr.write(
                    '(none): E: interrupted, exiting while reading %s\n' % arg)
                sys.exit(2)
            except Exception, e:
                if isfile:
                    arg = os.path.abspath(arg)
                sys.stderr.write(
                    '(none): E: error while reading %s: %s\n' % (arg, e))
                pkgs = []
                continue

            for pkg in pkgs:
                runChecks(pkg)
                packages_checked += 1

        for dname in dirs:
            try:
                for path, dirs, files in os.walk(dname):
                    for fname in files:
                        fname = os.path.abspath(os.path.join(path, fname))
                        try:
                            if fname.endswith('.rpm') or \
                               fname.endswith('.spm'):
                                pkg = Pkg.Pkg(fname, extract_dir)
                                runChecks(pkg)
                                packages_checked += 1

                            elif do_spec_check and fname.endswith('.spec'):
                                pkg = Pkg.FakePkg(fname)
                                check = SpecCheck.SpecCheck()
                                check.check_spec(pkg, fname)
                                pkg.cleanup()
                                specfiles_checked += 1

                        except KeyboardInterrupt:
                            sys.stderr.write(
                                '(none): E: interrupted, exiting while ' +
                                'reading %s\n' % fname)
                            sys.exit(2)
                        except Exception, e:
                            sys.stderr.write(
                                '(none): E: while reading %s: %s\n' %
                                (fname, e))
                            continue
            except Exception, e:
                sys.stderr.write(
                    '(none): E: error while reading dir %s: %s' % (dname, e))
                continue

        if printAllReasons():
            sys.stderr.write('(none): E: badness %d exceeds threshold %d, aborting.\n' % (badnessScore(), badnessThreshold()))
            sys.exit(66)

    finally:
        print "%d packages and %d specfiles checked; %d errors, %d warnings." \
              % (packages_checked, specfiles_checked,
                 printed_messages["E"], printed_messages["W"])

    if printed_messages["E"] > 0:
        sys.exit(64)
    sys.exit(0)

def runChecks(pkg):

    try:
        if verbose:
            printInfo(pkg, 'checking')

        for name in Config.allChecks():
            check = AbstractCheck.AbstractCheck.known_checks.get(name)
            if check:
                check.check(pkg)
            else:
                sys.stderr.write(
                    '(none): W: unknown check %s, skipping\n' % name)
    finally:
        pkg.cleanup()

#############################################################################
#
#############################################################################

sys.argv[0] = os.path.basename(sys.argv[0])

# parse options
try:
    (opt, args) = getopt.getopt(sys.argv[1:],
                              'iI:c:C:hVvanE:f:',
                              ['info',
                               'check=',
                               'checkdir=',
                               'help',
                               'version',
                               'verbose',
                               'all',
                               'noexception',
                               'extractdir=',
                               'file=',
                               ])
except getopt.error, e:
    sys.stderr.write("%s: %s\n" % (sys.argv[0], e))
    usage(sys.argv[0])
    sys.exit(1)

# process options
checkdir = '/usr/share/rpmlint'
checks = []
verbose = False
extract_dir = None
conf_file = _default_user_conf
if not os.path.exists(os.path.expanduser(conf_file)):
    # deprecated backwards compatibility with < 0.88
    conf_file = '~/.rpmlintrc'
info_error = None

# load global config files
configs = glob.glob('/etc/rpmlint/*config')
configs.sort()
configs.insert(0, '/usr/share/rpmlint/config')
for f in configs:
    try:
        execfile(f)
    except IOError:
        pass
    except Exception, E:
        sys.stderr.write('(none): W: error loading %s, skipping: %s\n' % (f, E))
# pychecker fix
del f

# process command line options
for o in opt:
    if o[0] == '-c' or o[0] == '--check':
        checks.append(o[1])
    elif o[0] == '-i' or o[0] == '--info':
        Config.info = True
    elif o[0] == '-I':
        info_error = o[1]
    elif o[0] == '-h' or o[0] == '--help':
        usage(sys.argv[0])
        sys.exit(0)
    elif o[0] == '-C' or o[0] == '--checkdir':
        Config.addCheckDir(o[1])
    elif o[0] == '-v' or o[0] == '--verbose':
        verbose = True
    elif o[0] == '-V' or o[0] == '--version':
        printVersion()
        sys.exit(0)
    elif o[0] == '-E' or o[0] == '--extractdir':
        extract_dir = o[1]
        Config.setOption('ExtractDir', extract_dir)
    elif o[0] == '-n' or o[0] == '--noexception':
        Config.no_exception = True
    elif o[0] == '-a' or o[0] == '--all':
        if '*' not in args:
            args.append('*')
    elif o[0] == '-f' or o[0] == '--file':
        conf_file = o[1]
    else:
        print 'unknown option', o

# load user config file
try:
    execfile(os.path.expanduser(conf_file))
except IOError:
    pass
except Exception,E:
    sys.stderr.write('(none): W: error loading %s, skipping: %s\n' % (conf_file, E))

if not extract_dir:
    extract_dir = Config.getOption('ExtractDir', tempfile.gettempdir())

if info_error:
    Config.info = True
    for c in checks:
        Config.addCheck(c)
    for c in Config.allChecks():
        loadCheck(c)
    for e in info_error.split(','):
        print "%s:" % e
        printDescriptions(e)
    sys.exit(0)

# if no argument print usage
if not args:
    usage(sys.argv[0])
    sys.exit(1)

if __name__ == '__main__':
    if checks:
        Config.resetChecks()
        for check in checks:
            Config.addCheck(check)
    main()

# rpmlint.py ends here

# Local variables:
# indent-tabs-mode: nil
# py-indent-offset: 4
# End:
# ex: ts=4 sw=4 et
