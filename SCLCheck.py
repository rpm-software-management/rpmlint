# -*- coding: utf-8 -*-
#############################################################################
# File          : SCLCheck.py
# Package       : rpmlint
# Author        : Miro Hrončok
# Created on    : Wed Jul 24 20:25 2013
# Purpose       : Software Collections checks.
#############################################################################

import rpm, re, os

from Filter import addDetails, printError, printWarning
from TagsCheck import VALID_GROUPS
import AbstractCheck
import Config
import Pkg
import Common

# Compile all regexes here
allowed_etc = re.compile(r'^/etc/(cron|profile|logrotate)\.d/', re.M)
allowed_var = re.compile(r'^/var/(log|lock)/', re.M)
buildrequires = re.compile(r'^BuildRequires:\s*(.*)', re.M)
global_scl_definition = re.compile(r'(^|\s)%(define|global)\s+scl\s+\S+\s*$',re.M)
libdir = re.compile(r'%\{?\??_libdir\}?', re.M)
name = re.compile(r'^Name:\s*(.*)', re.M)
name_small = re.compile(r'^%\{?name\}?', re.M)
noarch = re.compile(r'^BuildArch:\s*noarch\s*$', re.M)
obsoletes_conflicts = re.compile(r'^(Obsoletes|(Build)?Conflicts):\s*(.*)', re.M)
pkg_name = re.compile(r'(^|\s)%\{!\?scl:%(define|global)\s+pkg_name\s+%\{name\}\}\s*$', re.M)
provides = re.compile(r'^Provides:\s*(.*)', re.M)
requires = re.compile(r'(^|:)Requires:\s*(.*)', re.M)
scl_files = re.compile(r'(^|\s)%\{?\??scl_files\}?\s*$', re.M)
scl_install = re.compile(r'(^|\s)%\{?\??scl_install\}?\s*$', re.M)
scl_macros = re.compile(r'(^|\s)%\{?\??_root_sysconfdir\}?/rpm/macros\.%\{?\??scl\}?-config\s*^', re.M)
scl_package_definition = re.compile(r'(^|\s)%\{\?scl\s*:\s*%scl_package\s+\S+\s*\}\s*$',re.M)
scl_prefix_noncond = re.compile(r'%\{?scl_prefix\}?', re.M)
scl_prefix = re.compile(r'%\{?\??scl_prefix\}?', re.M)
scl_prefix_start = re.compile(r'^%\{?\??scl_prefix\}?', re.M)
scl_runtime = re.compile(r'%\{?\??scl\}?-runtime\}?', re.M)
scl_use = re.compile(r'%\{?\??\!?\??scl')
setup = re.compile(r'^%setup(.*)', re.M)
startdir = re.compile(r'^/opt/[^/]+/',re.M)
subpackage_alien = re.compile(r'(^|\s)%package\s+(-n\s+)?(?!(build|runtime))\S+\s*$',re.M)
subpackage_any = re.compile(r'(^|\s)%package\s+(.*)',re.M)
subpackage_build = re.compile(r'(^|\s)%package\s+build\s*$',re.M)
subpackage_runtime = re.compile(r'(^|\s)%package\s+runtime\s*$',re.M)


def index_or_sub(source, word, sub=0):
    '''Helper function that returns index of word in source or sub when not found'''
    try:
        return source.index(word)
    except:
        return sub

class SCLCheck(AbstractCheck.AbstractCheck):
    '''Software Collections checks'''

    def __init__(self):
        AbstractCheck.AbstractCheck.__init__(self, "SCLCheck")
        self._spec_file = None

    def check_source(self, pkg):
        # lookup spec file
        for fname, pkgfile in pkg.files().items():
            if fname.endswith('.spec'):
                self._spec_file = pkgfile.path
                self.check_spec(pkg, self._spec_file)
    
    def check_spec(self, pkg, spec_file, spec_lines=[]):
        '''SCL spec file checks'''
        spec = '\n'.join(Pkg.readlines(spec_file))
        if global_scl_definition.search(spec):
            self.check_metapackage(pkg, spec)
        elif scl_package_definition.search(spec):
            self.check_scl_spec(pkg, spec)
        elif scl_use.search(spec):
            printError(pkg, 'undeclared-scl')

    def check_binary(self, pkg):
        '''SCL binary package checks'''
        # Assume that no dash in package name means no SCL
        splits = pkg.name.split('-')
        if len(splits) < 2:
            return
        scl_name = splits[0]
        # While we are here, check if it's a runtime/build package
        is_runtime = splits[-1] == 'runtime'
        is_build = splits[-1] == 'build'
        del splits
        
        # Now test if there is /opt/foo/ dir
        good = False
        for fname in pkg.files().keys():
            if startdir.search(fname):
                good = True
                break
        if not good:
            return
        
        # Test if our dir is named the same way as scl
        good = True
        for fname in pkg.files().keys():
            if not startdir.search(fname):
                if allowed_etc.search(fname) or allowed_var.search(fname) or fname.startswith('/usr/bin/'):
                    continue
                if fname.startswith('/etc/rpm/'):
                    if not is_build:
                        printWarning(pkg, 'scl-rpm-macros-outside-of-build', fname)
                    continue
                if is_runtime and fname == os.path.join('/etc/scl/prefixes',scl_name):
                    continue
                printError(pkg, 'file-outside-of-scl-tree', fname)
            else:
                if fname.split('/')[3] != scl_name:
                    good = False
        
        if not good:
            printError(pkg, 'scl-name-screwed-up')

    def check_metapackage(self, pkg, spec):
        '''SCL metapackage spec checks'''
        
        # Examine subpackages
        runtime = subpackage_runtime.search(spec)
        if not runtime:
            printError(pkg, 'no-runtime-in-scl-metapackage')
        
        build = subpackage_build.search(spec)
        if not build:
            printError(pkg, 'no-build-in-scl-metapackage')
        else:
            # Get (B)Rs section for build subpackage
            end = index_or_sub(spec[build.end():],'%package',-1)
            if 'scl-utils-build' not in ' '.join(self.get_requires(spec[build.end():end])):
                printWarning(pkg, 'scl-build-without-requiring-scl-utils-build')
        
        alien = subpackage_alien.search(spec)
        if alien:
            printError(pkg, 'weird-subpackage-in-scl-metapackage', alien.group()[9:])
        
        # Get (B)Rs section for main package
        end = index_or_sub(spec,'%package',-1)
        if 'scl-utils-build' not in ' '.join(self.get_build_requires(spec[:end])):
            printError(pkg, 'scl-metapackage-without-scl-utils-build-br')
        
        # Enter %install section
        install_start = index_or_sub(spec,'%install')
        install_end = index_or_sub(spec,'%check')
        if not install_end: install_end = index_or_sub(spec,'%clean')
        if not install_end: install_end = index_or_sub(spec,'%files')
        if not install_end: install_end = index_or_sub(spec,'%changelog',-1)
        # Search %scl_install
        if not scl_install.search(spec[install_start:install_end]):
            printError(pkg, 'scl-metapackage-without-%scl_install')
        if noarch.search(spec[:install_start]) and libdir.search(spec[install_start:install_end]):
            printError(pkg, 'noarch-scl-metapackage-with-libdir')
        
        # Analyze %files
        files = self.get_files(spec)
        if files:
            printWarning(pkg, 'scl-main-metapackage-contains-files', ', '.join(files))
        if runtime:
            if not scl_files.search('\n'.join(self.get_files(spec,'runtime'))):
                printError(pkg, 'scl-runtime-package-without-%scl_files')
        if build:
            if not scl_macros.search('\n'.join(self.get_files(spec,'build'))):
                printError(pkg, 'scl-build-package-without-rpm-macros')
    
    def check_scl_spec(self, pkg, spec):
        '''SCL ready spec checks'''
        
        # For the entire spec
        if not pkg_name.search(spec):
            printWarning(pkg, 'missing-pkg_name-definition')
        if scl_prefix_noncond.search(self.remove_scl_conds(spec)):
            printWarning(pkg, 'scl-prefix-without-condition')
        if not scl_prefix.search(self.get_name(spec)):
            printError(pkg, 'name-without-scl-prefix')
        for item in self.get_obsoletes_and_conflicts(spec):
            if not scl_prefix.search(item):
                printError(pkg, 'obsoletes-or-conflicts-without-scl-prefix')
                break
        for item in self.get_provides(spec):
            if not scl_prefix.search(item):
                printError(pkg, 'provides-without-scl-prefix')
                break
        setup_opts = setup.search(spec)
        if setup_opts:
            if '-n' not in setup_opts.groups()[0]:
                printError(pkg, 'scl-setup-without-n')
        
        # Examine main package and subpackages one by one
        borders = []
        borders.append(0) # main package starts at the beginning
        while True:
            more = subpackage_any.search(spec[borders[-1]:])
            if not more: break
            splits = more.groups()[1].split()
            if len(splits) > 1 and splits[0] == '-n':
                if not scl_prefix_start.search(splits[-1]):
                    printError(pkg, 'subpackage-with-n-without-scl-prefix')
            borders.append(borders[-1]+more.end()) # current end is counted only from last one
        subpackages = [(borders[i],borders[i+1]) for i in range(len(borders)-1)]
        for subpackage in subpackages:
            ok = False
            for require in self.get_requires(spec[subpackage[0]:subpackage[1]]):
                # Remove flase entries
                if not require or require == ':': continue
                # If it starts with %{name}, it,s fine
                # If it starts with SCL prefix, it's fine
                # If it is scl-runtime, it's the best
                if name_small.search(require) or scl_prefix_start.search(require) or scl_runtime.match(require):
                    ok = True
                    break
            if not ok:
                printError(pkg, 'doesnt-require-scl-runtime-or-other-scl-package')
                break
        
    
    def get_requires(self, text, build=False):
        '''For given piece of spec, find Requires (or BuildRequires)'''
        if build:
            search = buildrequires
        else:
            search = requires
        res = []
        while True:
            more = search.search(text)
            if not more: break
            res.extend(more.groups())
            text = text[more.end():]
        return res
        
    def get_build_requires(self, text):
        '''Call get_requires() with build = True'''
        return self.get_requires(text,True)
    
    def get_name(self, text):
        '''For given piece of spec, get the Name of the main package'''
        sname = name.search(text)
        if not sname: return None
        return sname.groups()[0].strip()
    
    def get_obsoletes_and_conflicts(self, text):
        '''For given piece of spec, find Obsoletes and Conflicts'''
        res = []
        while True:
            more = obsoletes_conflicts.search(text)
            if not more: break
            res.extend(more.groups()[2:]) # first group is either 'Obsoletes' or 'Conflicts', second is Build or None
            text = text[more.end():]
        return res
    
    def get_provides(self, text):
        '''For given piece of spec, find Provides'''
        res = []
        while True:
            more = provides.search(text)
            if not more: break
            res.extend(more.groups())
            text = text[more.end():]
        return res
    
    def get_files(self, text, subpackage=None):
        '''Return the list of files in %files section for given subpackage or main package'''
        if subpackage:
            pattern = r'%\{?\??files\}?(\s+-n)?\s+'+subpackage+r'\s*$'
        else:
            pattern = r'%\{?\??files\}?\s*$'
        search = re.search(pattern, text, re.M)
        if not search: return []
        
        start = search.end()
        end = index_or_sub(text[start:],'%files')
        if not end: end = index_or_sub(text[start:],'%changelog',-1)
        return list(filter(None, text[start:start+end].strip().split('\n')))
    
    def remove_scl_conds(self, text):
        '''Returns given text without %scl conds blocks'''
        while text.count('%{?scl:') > 0:
            spos = text.index('%{?scl:')
            pos = spos+7
            counter = 1
            while counter:
                if text[pos] == '{': counter += 1
                if text[pos] == '}': counter -= 1
                pos += 1
            text = text[:spos]+text[pos:]
        return text
        

# Create an object to enable the auto registration of the test
check = SCLCheck()

# Add information about checks
addDetails(
'undeclared-scl',
'SPEC contains %scl* macros, but was not recognized as SCL metapackage or SCL ready package. If this should be SCL metapackage, don\'t forget to define %scl macro. If this should be SCL ready package, run %scl conditionalized %scl_package macro, e.g. %{?scl:%scl_package foo}.'

'no-runtime-in-scl-metapackage',
'SCL metapackage must have runtime subpackage',

'no-build-in-scl-metapackage',
'SCL metapackage must have build subpackage',

'weird-subpackage-in-scl-metapackage',
'Only allowed subpackages in SCL metapackage are build and runtime'

'scl-metapackage-without-scl-utils-build-br',
'SCL metapackage must BuildRequire scl-utils-build',

'scl-build-without-requiring-scl-utils-build',
'SCL runtime package should Require scl-utils-build',

'scl-metapackage-without-%scl_install',
'SCL metapackage must call %scl_install in the %install section',

'noarch-scl-metapackage-with-libdir',
'If "enable" script of SCL metapackage contains %{_libdir}, the package must be arch specific, otherwise it may be noarch',

'scl-main-metapackage-contains-files',
'Main package of SCL metapackage should not contain any files',

'scl-runtime-package-without-%scl_files',
'SCL runtime package must contain %scl_files in %files section',

'scl-build-package-without-rpm-macros',
'SCL build package must contain %{_root_sysconfdir}/rpm/macros.%{scl}-config in %files section',

'missing-pkg_name-definition',
'%{!?scl:%global pkg_name %{name}} is missing in the spec',

'name-without-scl-prefix',
'Name of SCL package must start with %{?scl_prefix}',

'scl-prefix-without-condition',
'The SCL prefix is used without condition - this won\'t work if the package is build outside of SCL - use %{?scl_prefix} with questionmark',

'obsoletes-or-conflicts-without-scl-prefix',
'Obsoletes, Conflicts and Build Conflicts must always be prefixed with %{?scl_prefix}. This is extremely important, as the SCLs are often used for deploying new packages on older systems (that may contain old packages, now obsoleted by the new ones), but they shouldn\'t Obsolete or Conflict with the non-SCL RPMs installed on the system (that\'s the idea of SCL)',

'provides-without-scl-prefix',
'Provides tag must always be prefixed with %{?scl_prefix}',

'doesnt-require-scl-runtime-or-other-scl-package',
'The package must require %{scl}-runtime, unless it depends on another package that requires %{scl}-runtime. It\'s impossible to check what other packages require, so this simply checks if this package requires at least something from its collection',

'subpackage-with-n-without-scl-prefix',
'If (and only if) a package define its name with -n, the name must be prefixed with %{?scl_prefix}',

'scl-setup-without-n',
'The %setup macro need the -n argument for SCL builds, cause the directory with source probably doesn\'t include SCL prefix in its name',

'scl-name-screwed-up',
'SCl package\'s name starts with SCL prefix. That prefix is used as a directory, where files are stored: If the prefix is foo, the directory is /opt/provides/foo. This package doesn\'t respect that. This means either the name of the package is wrong, or the directory',

'file-outside-of-scl-tree',
'SCL package should only contain files in /opt/provider/scl-name directory or in other allowed directories such as some directories in /etc or /var. wrapper scripts in /usr/bin are also allowed',

'scl-rpm-macros-outside-of-build',
'RPM macros in SCL packages shoul belong to -build subpackage of the SCL metapackage'
)
