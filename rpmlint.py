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
import os
import stat
import sys
import tempfile

import rpm

from Filter import printAllReasons, printError, printInfo, printWarning, \
     printed_messages
import AbstractCheck
import Config
import Pkg
import SpecCheck


version = '@VERSION@'

# Print usage information
def usage(name):
    print 'usage:', name, \
          '[<options>] <rpm files|installed packages|specfiles|dirs>'
    print '  options in:'
    print '\t[-i|--info]\n\t[-I <error,error,...>]\n\t[-c|--check <check>]\n\t[-a|--all]\n\t[-C|--checkdir <checkdir>]\n\t[-h|--help]\n\t[-v|--verbose]\n\t[-E|--extractdir <dir>]\n\t[-V|--version]\n\t[-n|--noexception]\n\t[-f|--file <config file to use instead of ~/.rpmlintrc>]'

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

    # Add check dirs to the front of load path
    sys.path[0:0] = Config.checkDirs()

    # Load all checks
    for c in Config.allChecks():
        loadCheck(c)

    packages_checked = 0
    specfiles_checked = 0

    pkg = None
    try:
        # Loop over all file names given in arguments
        dirs = []
        for f in args:
            pkgs = []
            isfile = False
            try:
                try:
                    st = os.stat(f)
                    isfile = True
                    if stat.S_ISREG(st[stat.ST_MODE]):
                        if not f.endswith(".spec"):
                            pkgs.append(Pkg.Pkg(f, extract_dir))
                        elif 'SpecCheck' in Config.allChecks():
                            # Short-circuit spec file checks
                            pkg = Pkg.FakePkg(f)
                            check = SpecCheck.SpecCheck()
                            check.check_spec(pkg, f)
                            specfiles_checked += 1

                    elif stat.S_ISDIR(st[stat.ST_MODE]):
                        dirs.append(f)
                        continue
                    else:
                        raise OSError
                except OSError:
                    ipkgs = Pkg.getInstalledPkgs(f)
                    if not ipkgs:
                        sys.stderr.write(
                            '(none): E: no installed packages by name %s\n' % f)
                    else:
                        pkgs.extend(ipkgs)
            except KeyboardInterrupt:
                if isfile:
                    f = os.path.abspath(f)
                sys.stderr.write('(none): E: interrupted, exiting while reading %s\n' % f)
                sys.exit(2)
            except Exception, e:
                if isfile:
                    f = os.path.abspath(f)
                sys.stderr.write('(none): E: error while reading %s: %s\n' % (f, e))
                pkgs = []
                continue

            for pkg in pkgs:
                runChecks(pkg)
                packages_checked += 1
                pkg.cleanup()

        for d in dirs:
            try:
                for i in os.listdir(d):
                    f = os.path.abspath(os.path.join(d, i))
                    st = os.stat(f)
                    if stat.S_ISREG(st[stat.ST_MODE]):
                        if not (f.endswith('.rpm') or f.endswith('.spm') or \
                                f.endswith('.spec')):
                            continue
                        try:
                            if f.endswith('.spec'):
                                if 'SpecCheck' in Config.allChecks():
                                    pkg = Pkg.FakePkg(f)
                                    check = SpecCheck.SpecCheck()
                                    check.check_spec(pkg, f)
                                    specfiles_checked += 1
                            else:
                                pkg = Pkg.Pkg(f, extract_dir)
                                runChecks(pkg)
                                packages_checked += 1
                        except KeyboardInterrupt:
                            sys.stderr.write('(none): E: interrupted, exiting while reading %s\n' % f)
                            sys.exit(2)
                        except Exception, e:
                            sys.stderr.write(
                                '(none): E: while reading %s: %s\n' % (f, e))
                            pkg = None
                            continue
            except Exception, e:
                sys.stderr.write(
                    '(none): E: error while reading dir %s: %s' % (d, e))
                pkg = None
                continue

        # if requested, scan all the installed packages
        if allpkgs:
            try:
                if Pkg.v42:
                    ts = rpm.TransactionSet('/')
                    for item in ts.dbMatch():
                        pkg = Pkg.InstalledPkg(item[rpm.RPMTAG_NAME], item)
                        runChecks(pkg)
                        packages_checked += 1
                else:
                    try:
                        db = rpm.opendb()
                        idx = db.firstkey()
                        while idx:
                            pkg = Pkg.InstalledPkg(db[idx][rpm.RPMTAG_NAME], db[idx])
                            runChecks(pkg)
                            packages_checked += 1
                            idx = db.nextkey(idx)
                    finally:
                        del db
            except KeyboardInterrupt:
                sys.stderr.write('(none): E: interrupted, exiting while scanning all packages\n')
                sys.exit(2)

        if printAllReasons():
            sys.stderr.write('(none): E: badness %d exceeds threshold %d, aborting.\n' % (badnessScore(), badnessThreshold()))
            sys.exit(66)

    finally:
        pkg and pkg.cleanup()
        print "%d packages and %d specfiles checked; %d errors, %d warnings." \
              % (packages_checked, specfiles_checked,
                 printed_messages["E"], printed_messages["W"])

    if printed_messages["E"] > 0:
        sys.exit(64)
    sys.exit(0)

def runChecks(pkg):

    if verbose:
        printInfo(pkg, 'checking')

    for name in Config.allChecks():
        check = AbstractCheck.AbstractCheck.known_checks.get(name)
        if check:
            check.check(pkg)
        else:
            sys.stderr.write('(none): W: unknown check %s, skipping\n' % name)

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
verbose = 0
extract_dir = None
allpkgs = 0
conf_file = '~/.rpmlintrc'
info_error = 0

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
        Config.info = 1
    elif o[0] == '-I':
        info_error = o[1]
    elif o[0] == '-h' or o[0] == '--help':
        usage(sys.argv[0])
        sys.exit(0)
    elif o[0] == '-C' or o[0] == '--checkdir':
        Config.addCheckDir(o[1])
    elif o[0] == '-v' or o[0] == '--verbose':
        verbose = 1
    elif o[0] == '-V' or o[0] == '--version':
        printVersion()
        sys.exit(0)
    elif o[0] == '-E' or o[0] == '--extractdir':
        extract_dir = o[1]
        Config.setOption('ExtractDir', extract_dir)
    elif o[0] == '-n' or o[0] == '--noexception':
        Config.no_exception = 1
    elif o[0] == '-a' or o[0] == '--all':
        allpkgs = 1
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
    Config.info = 1
    for c in checks:
        Config.addCheck(c)
    for c in Config.allChecks():
        loadCheck(c)
    for e in info_error.split(','):
        print "%s:" % e
        printDescriptions(e)
    sys.exit(0)

# if no argument print usage
if args == [] and not allpkgs:
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
