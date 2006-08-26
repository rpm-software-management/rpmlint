#############################################################################
# File          : BinariesCheck.py
# Package       : rpmlint
# Author        : Frederic Lepied
# Created on    : Tue Sep 28 07:01:42 1999
# Version       : $Id$
# Purpose       : check binary files in a binary rpm package.
#############################################################################

from Filter import *
import AbstractCheck
import rpm
import re
import commands
import string
import sys
import Config
import Pkg
import stat

DEFAULT_SYSTEM_LIB_PATHS=('/lib', '/usr/lib', '/usr/X11R6/lib',
                          '/lib64', '/usr/lib64', '/usr/X11R6/lib64')

class BinaryInfo:

    needed_regex=re.compile('^\s*NEEDED\s*(\S+)')
    rpath_regex=re.compile('^\s*RPATH\s*(\S+)')
    soname_regex=re.compile('^\s*SONAME\s*(\S+)')
    comment_regex=re.compile('^\s*\d+\s+\.comment\s+')
    dynsyms_regex=re.compile('^DYNAMIC SYMBOL TABLE:')
    pic_regex=re.compile('^\s+\d+\s+\.rela?\.(data|text)')
    non_pic_regex=re.compile('TEXTREL', re.MULTILINE)
    undef_regex=re.compile('^undefined symbol:\s+(\S+)')
    debug_file_regex=re.compile('\.debug$')

    def __init__(self, pkg, path, file):
        self.objdump_error=0
        self.needed=[]
        self.rpath=[]
        self.undef=[]
        self.comment=0
        self.dynsyms=0
        self.soname=0
        self.non_pic=1

        is_debug=BinaryInfo.debug_file_regex.search(path)

        topt=not is_debug and '-T' or ''
        res=commands.getstatusoutput('LC_ALL=C objdump --headers --private-headers %s %s' % (topt, path))
        if not res[0]:
            for l in string.split(res[1], '\n'):
                needed=BinaryInfo.needed_regex.search(l)
                if needed:
                    self.needed.append(needed.group(1))
                else:
                    rpath=BinaryInfo.rpath_regex.search(l)
                    if rpath:
                        for p in string.split(rpath.group(1), ':'):
                            self.rpath.append(p)
                    elif BinaryInfo.comment_regex.search(l):
                        self.comment=1
                    elif BinaryInfo.dynsyms_regex.search(l):
                        self.dynsyms=1
                    elif BinaryInfo.pic_regex.search(l):
                        self.non_pic=0
                    r=BinaryInfo.soname_regex.search(l)
                    if r:
                        self.soname=r.group(1)
            if self.non_pic:
                self.non_pic=BinaryInfo.non_pic_regex.search(res[1])
        else:
            self.objdump_error=1
            printWarning(pkg, 'objdump-failed', re.sub('\n.*', '', res[1]))

        # undefined symbol check makes sense only for installed packages
        # skip debuginfo: https://bugzilla.redhat.com/190599
        if not is_debug and isinstance(pkg, Pkg.InstalledPkg):
            # We could do this with objdump, but it's _much_ simpler with ldd.
            res=commands.getstatusoutput('LC_ALL=C ldd -d -r %s' % path)
            if not res[0]:
                for l in string.split(res[1], '\n'):
                    undef=BinaryInfo.undef_regex.search(l)
                    if undef:
                        self.undef.append(undef.group(1))
            else:
                printWarning(pkg, 'ldd-failed', file)

path_regex=re.compile('(.*/)([^/]+)')
numeric_dir_regex=re.compile('/usr(?:/share)/man/man./(.*)\.[0-9](?:\.gz|\.bz2)')
versioned_dir_regex=re.compile('[^.][0-9]')
binary_regex=re.compile('ELF|current ar archive')
usr_share=re.compile('^/usr/share/')
etc=re.compile('^/etc/')
not_stripped=re.compile('not stripped')
unstrippable=re.compile('\.o$|\.static$')
shared_object_regex=re.compile('shared object')
executable_regex=re.compile('executable')
libc_regex=re.compile('libc\.')
ldso_soname_regex=re.compile('^ld(-linux(-(ia|x86_)64))?\.so')
so_regex=re.compile('/lib(64)?/[^/]+\.so(\.[0-9]+)*$')
validso_regex=re.compile('^lib.+(\.so\.[\.0-9]+|-[\.0-9]+\.so)$')
sparc_regex=re.compile('SPARC32PLUS|SPARC V9|UltraSPARC')
system_lib_paths=Config.getOption('SystemLibPaths', DEFAULT_SYSTEM_LIB_PATHS)
usr_lib_regex=re.compile('^/usr/lib(64)?/')
bin_regex=re.compile('^(/usr(/X11R6)?)?/s?bin/')
soversion_regex=re.compile('.*?([0-9][.0-9]*)\\.so|.*\\.so\\.([0-9][.0-9]*).*')
reference_regex=re.compile('\.la$|^/usr/lib(64)?/pkgconfig/')
usr_lib_exception_regex=re.compile(Config.getOption('UsrLibBinaryException', '^/usr/lib(64)?/(perl|python|ruby|menu|pkgconfig|lib[^/]+\.(so|l?a)$|bonobo/servers/)'))
srcname_regex=re.compile('(.*?)-[0-9]')

def dir_base(path):
    res=path_regex.search(path)
    if res:
        return res.group(1), res.group(2)
    else:
        return '', path

class BinariesCheck(AbstractCheck.AbstractCheck):

    def __init__(self):
        AbstractCheck.AbstractCheck.__init__(self, 'BinariesCheck')

    def check(self, pkg):
        # Check only binary package
        if pkg.isSource():
            return

        info=pkg.getFilesInfo()
        arch=pkg[rpm.RPMTAG_ARCH]
        files=pkg.files()
        exec_files=[]
        has_lib=[]
        version=None
        binary=0
        binary_in_usr_lib=0
        has_usr_lib_file=0

        res=srcname_regex.search(pkg[rpm.RPMTAG_SOURCERPM])
        if res:
            multi_pkg=(pkg.name != res.group(1))
        else:
            multi_pkg=0

        for f in files.keys():
            if usr_lib_regex.search(f) and not usr_lib_exception_regex.search(f) and not stat.S_ISDIR(files[f][0]):
                has_usr_lib_file=f
                break

        for i in info:
            is_binary=binary_regex.search(i[1])

            if is_binary:
                binary=binary+1
                if has_usr_lib_file and not binary_in_usr_lib and usr_lib_regex.search(i[0]):
                    binary_in_usr_lib=1

                if arch == 'noarch':
                    printError(pkg, 'arch-independent-package-contains-binary-or-object', i[0])
                else:
                    # in /usr/share ?
                    if usr_share.search(i[0]):
                        printError(pkg, 'arch-dependent-file-in-usr-share', i[0])
                    # in /etc ?
                    if etc.search(i[0]):
                        printError(pkg, 'binary-in-etc', i[0])

                    if arch == 'sparc' and sparc_regex.search(i[1]):
                        printError(pkg, 'non-sparc32-binary', i[0])

                    # stripped ?
                    if not unstrippable.search(i[0]):
                        if not_stripped.search(i[1]):
                            printWarning(pkg, 'unstripped-binary-or-object', i[0])

                        # inspect binary file
                        bin_info=BinaryInfo(pkg, pkg.dirName()+i[0], i[0])

                        # so name in library
                        if so_regex.search(i[0]):
                            has_lib.append(i[0])
                            if bin_info.objdump_error:
                                pass
                            elif not bin_info.soname:
                                printWarning(pkg, 'no-soname', i[0])
                            else:
                                if not validso_regex.search(bin_info.soname):
                                    printError(pkg, 'invalid-soname', i[0], bin_info.soname)
                                else:
                                    (directory, base) = dir_base(i[0])
                                    try:
                                        symlink = directory + bin_info.soname
                                        (perm, owner, group, link, size, md5, mtime, rdev) = files[symlink]
                                        if link != i[0] and link != base and link != '':
                                            printError(pkg, 'invalid-ldconfig-symlink', i[0], link)
                                    except KeyError:
                                        printError(pkg, 'no-ldconfig-symlink', i[0])
                                res=soversion_regex.search(bin_info.soname)
                                if res:
                                    soversion=res.group(1) or res.group(2)
                                    if version == None:
                                        version = soversion
                                    elif version != soversion:
                                        version = -1

                            if bin_info.non_pic:
                                printError(pkg, 'shlib-with-non-pic-code', i[0])
                        # rpath ?
                        if bin_info.rpath:
                            for p in bin_info.rpath:
                                if p in system_lib_paths or \
                                   not usr_lib_regex.search(p):
                                    printError(pkg, 'binary-or-shlib-defines-rpath', i[0], bin_info.rpath)
                                    break

                        # statically linked ?
                        is_exec=executable_regex.search(i[1])
                        if shared_object_regex.search(i[1]) or \
                           is_exec:

                            if is_exec and bin_regex.search(i[0]):
                                exec_files.append(i[0])

                            if bin_info.objdump_error:
                                pass
                            elif not bin_info.needed and \
                               not (bin_info.soname and \
                                    ldso_soname_regex.search(bin_info.soname)):
                                if shared_object_regex.search(i[1]):
                                    printError(pkg, 'shared-lib-without-dependency-information', i[0])
                                else:
                                    printError(pkg, 'statically-linked-binary', i[0])
                            else:
                                # linked against libc ?
                                if not libc_regex.search(i[0]) and \
                                   ( not bin_info.soname or \
                                     ( not libc_regex.search(bin_info.soname) and \
                                       not ldso_soname_regex.search(bin_info.soname))):
                                    found_libc=0
                                    for lib in bin_info.needed:
                                        if libc_regex.search(lib):
                                            found_libc=1
                                            break
                                    if not found_libc:
                                        if shared_object_regex.search(i[1]):
                                            printError(pkg, 'library-not-linked-against-libc', i[0])
                                        else:
                                            printError(pkg, 'program-not-linked-against-libc', i[0])
                            # It could be useful to check this for
                            # non-shared-libs too, but that has potential to
                            # generate lots of false positives and noise.
                            if bin_info.undef and so_regex.search(i[0]):
                                for s in bin_info.undef:
                                    printWarning(pkg, 'undefined-non-weak-symbol', i[0], s)
            else:
                if reference_regex.search(i[0]):
                    lines = pkg.grep(re.compile('tmp|home'), i[0])
                    if lines:
                        printError(pkg, 'invalid-directory-reference', i[0],
                                   '(line %s)' % ", ".join(lines))

        if has_lib != []:
            if exec_files != []:
                for f in exec_files:
                    printError(pkg, 'executable-in-library-package', f)
            for f in files.keys():
                res=numeric_dir_regex.search(f)
                fn=res and res.group(1) or f
                if not f in exec_files and not so_regex.search(f) and not versioned_dir_regex.search(fn):
                    printError(pkg, 'non-versioned-file-in-library-package', f)
            if version and version != -1 and string.find(pkg.name, version) == -1:
                printError(pkg, 'incoherent-version-in-name', version)

        if arch != 'noarch' and not multi_pkg:
            if binary == 0:
                printError(pkg, 'no-binary')

        if has_usr_lib_file and not binary_in_usr_lib:
            printError(pkg, 'only-non-binary-in-usr-lib')

# Create an object to enable the auto registration of the test
check=BinariesCheck()

# Add information about checks
if Config.info:
    addDetails(
'arch-independent-package-contains-binary-or-object',
'''The package contains a binary or object file but is tagged
noarch.''',

'arch-dependent-file-in-usr-share',
'''This package installs an ELF binary in the /usr/share
 hierarchy, which is reserved for architecture-independent files.''',

'binary-in-etc',
'''This package installs an ELF binary in /etc.  Both the
FHS and the FSSTND forbid this.''',

# 'non-sparc32-binary',
# '',

'invalid-soname',
'''The soname of the library is neither of the form lib<libname>.so.<major> or
lib<libname>-<major>.so.''',

'invalid-ldconfig-symlink',
'''The symbolic link references the wrong file. It should reference
the shared library.''',

'no-ldconfig-symlink',
'''The package should not only include the shared library itself, but
also the symbolic link which ldconfig would produce. (This is
necessary, so that the link gets removed by rpm automatically when
the package gets removed, even if for some reason ldconfig would not be
run at package postinstall phase.)''',

'shlib-with-non-pic-code',
'''The listed shared libraries contain object code that was compiled
without -fPIC. All object code in shared libraries should be
recompiled separately from the static libraries with the -fPIC option.

Another common mistake that causes this problem is linking with
``gcc -Wl,-shared'' instead of ``gcc -shared''.''',

'binary-or-shlib-defines-rpath',
'''The binary or shared library defines `RPATH'. Usually this is a
bad thing because it hardcodes the path to search libraries and so
makes it difficult to move libraries around.  Most likely you will find a
Makefile with a line like: gcc test.o -o test -Wl,--rpath.  Also, sometimes
configure scripts provide a --disable-rpath flag to avoid this.''',

'statically-linked-binary',
'''The package installs a statically linked binary or object file.

Usually this is a packaging bug. If not, contact your rpmlint distributor
about this so that this error gets included in the exception file for rpmlint
and will not be flagged as a packaging bug in the future (or add it to your
local configuration if you installed rpmlint from the source tarball).''',

'executable-in-library-package',
'''The package mixes up libraries and executables. Mixing up these
both types of files makes upgrades quite impossible.''',

'non-versioned-file-in-library-package',
'''The package contains files in non versioned directories. This makes it
impossible to have multiple major versions of the libraries installed.
One solution can be to change the directories which contain the files
to subdirs of /usr/lib/<name>-<version> or /usr/share/<name>-<version>.
Another solution can be to include a version number in the file names
themselves.''',

'incoherent-version-in-name',
'''The package name should contain the major version of the library.''',

'invalid-directory-reference',
'This file contains a reference to /tmp or /home.',

'no-binary',
'''The package should be of the noarch architecture because it doesn't contain
any binaries.''',

# http://sources.redhat.com/ml/libc-alpha/2003-05/msg00034.html
'undefined-non-weak-symbol',
'''The binary contains undefined non-weak symbols.  This may indicate improper
linkage; check that the binary has been linked as expected.''',

'only-non-binary-in-usr-lib',
'''There are only non binary files in /usr/lib so they should be in /usr/share.''',

'objdump-failed',
'''Executing objdump on this file failed, all checks could not be run.''',

'ldd-failed',
'''Executing ldd on this file failed, all checks could not be run.''',
)

# BinariesCheck.py ends here

# Local variables:
# indent-tabs-mode: nil
# py-indent-offset: 4
# End:
# ex: ts=4 sw=4 et
