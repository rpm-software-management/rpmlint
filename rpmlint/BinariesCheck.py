# -*- coding: utf-8 -*-
#############################################################################
# File          : BinariesCheck.py
# Package       : rpmlint
# Author        : Frederic Lepied
# Created on    : Tue Sep 28 07:01:42 1999
# Purpose       : check binary files in a binary rpm package.
#############################################################################

import os
import re
import stat
import subprocess

import rpm

import rpmlint.AbstractCheck as AbstractCheck
import rpmlint.Config as Config
import rpmlint.Pkg as Pkg
from rpmlint.Filter import addDetails, printError, printWarning


DEFAULT_SYSTEM_LIB_PATHS = (
    '/lib', '/usr/lib', '/usr/X11R6/lib',
    '/lib64', '/usr/lib64', '/usr/X11R6/lib64')


def create_regexp_call(call):
    r = r".*?\s+(%s(?:@GLIBC\S+)?)(?:\s|$)" % call
    return re.compile(r)


def create_nonlibc_regexp_call(call):
    r = r".*?\s+UND\s+(%s)\s?.*$" % call
    return re.compile(r)


class BinaryInfo(object):

    needed_regex = re.compile(r'\s+\(NEEDED\).*\[(\S+)\]')
    rpath_regex = re.compile(r'\s+\(RPATH\).*\[(\S+)\]')
    soname_regex = re.compile(r'\s+\(SONAME\).*\[(\S+)\]')
    comment_regex = re.compile(r'^\s+\[\s*\d+\]\s+\.comment\s+')
    pic_regex = re.compile(r'^\s+\[\s*\d+\]\s+\.rela?\.(data|text)')
    #   GNU_STACK      0x000000 0x00000000 0x00000000 0x00000 0x00000 RWE 0x4
    stack_regex = re.compile(r'^\s+GNU_STACK\s+(?:(?:\S+\s+){5}(\S+)\s+)?')
    stack_exec_regex = re.compile(r'^..E$')
    undef_regex = re.compile(r'^undefined symbol:\s+(\S+)')
    unused_regex = re.compile(r'^\s+(\S+)')
    call_regex = re.compile(r'\s0\s+FUNC\s+(.*)')
    exit_call_regex = create_regexp_call(r'_?exit')
    fork_call_regex = create_regexp_call(r'fork')
    setgid_call_regex = create_regexp_call(r'set(?:res|e)?gid')
    setuid_call_regex = create_regexp_call(r'set(?:res|e)?uid')
    setgroups_call_regex = create_regexp_call(r'(?:ini|se)tgroups')
    chroot_call_regex = create_regexp_call('chroot')

    forbidden_functions = Config.getOption("WarnOnFunction")
    if forbidden_functions:
        for name, func in forbidden_functions.items():
            # precompile regexps
            f_name = func['f_name']
            func['f_regex'] = create_nonlibc_regexp_call(f_name)
            if 'good_param' in func:
                func['waiver_regex'] = re.compile(func['good_param'])
            # register descriptions
            addDetails(name, func['description'])

    chdir_call_regex = create_regexp_call('chdir')
    mktemp_call_regex = create_regexp_call('mktemp')

    def __init__(self, pkg, path, fname, is_ar, is_shlib):
        self.readelf_error = False
        self.needed = []
        self.rpath = []
        self.undef = []
        self.unused = []
        self.comment = False
        self.soname = False
        self.non_pic = True
        self.stack = False
        self.exec_stack = False
        self.exit_calls = []
        self.forbidden_calls = []
        fork_called = False
        self.tail = ''

        self.setgid = False
        self.setuid = False
        self.setgroups = False
        self.chroot = False
        self.chdir = False
        self.chroot_near_chdir = False
        self.mktemp = False

        is_debug = path.endswith('.debug')
        # Currently this implementation works only on specific
        # architectures due to reliance on arch specific assembly.
        if (pkg.arch.startswith('armv') or pkg.arch == 'aarch64'):
            # 10450:   ebffffec        bl      10408 <chroot@plt>
            BinaryInfo.objdump_call_regex = re.compile(br'\sbl\s+(.*)')
        elif (pkg.arch.endswith('86') or pkg.arch == 'x86_64'):
            # 401eb8:   e8 c3 f0 ff ff          callq  400f80 <chdir@plt>
            BinaryInfo.objdump_call_regex = re.compile(br'callq?\s(.*)')
        else:
            BinaryInfo.objdump_call_regex = None

        res = Pkg.getstatusoutput(
            ('readelf', '-W', '-S', '-l', '-d', '-s', path))
        if not res[0]:
            lines = res[1].splitlines()
            for line in lines:
                r = BinaryInfo.needed_regex.search(line)
                if r:
                    self.needed.append(r.group(1))
                    continue

                r = BinaryInfo.rpath_regex.search(line)
                if r:
                    for p in r.group(1).split(':'):
                        self.rpath.append(p)
                    continue

                if BinaryInfo.comment_regex.search(line):
                    self.comment = True
                    continue

                if BinaryInfo.pic_regex.search(line):
                    self.non_pic = False
                    continue

                r = BinaryInfo.soname_regex.search(line)
                if r:
                    self.soname = r.group(1)
                    continue

                r = BinaryInfo.stack_regex.search(line)
                if r:
                    self.stack = True
                    flags = r.group(1)
                    if flags and BinaryInfo.stack_exec_regex.search(flags):
                        self.exec_stack = True
                    continue

                if line.startswith("Symbol table"):
                    break

            for line in lines:
                r = BinaryInfo.call_regex.search(line)
                if not r:
                    continue
                line = r.group(1)

                if BinaryInfo.mktemp_call_regex.search(line):
                    self.mktemp = True

                if BinaryInfo.setgid_call_regex.search(line):
                    self.setgid = True

                if BinaryInfo.setuid_call_regex.search(line):
                    self.setuid = True

                if BinaryInfo.setgroups_call_regex.search(line):
                    self.setgroups = True

                if BinaryInfo.chdir_call_regex.search(line):
                    self.chdir = True

                if BinaryInfo.chroot_call_regex.search(line):
                    self.chroot = True

                if BinaryInfo.forbidden_functions:
                    for r_name, func in BinaryInfo.forbidden_functions.items():
                        ret = func['f_regex'].search(line)
                        if ret:
                            self.forbidden_calls.append(r_name)

                if is_shlib:
                    r = BinaryInfo.exit_call_regex.search(line)
                    if r:
                        self.exit_calls.append(r.group(1))
                        continue
                    r = BinaryInfo.fork_call_regex.search(line)
                    if r:
                        fork_called = True
                        continue

            # check if we don't have a string that will automatically
            # waive the presence of a forbidden call
            if self.forbidden_calls:
                res = Pkg.getstatusoutput(('strings', path))
                if not res[0]:
                    for line in res[1].splitlines():
                        # as we need to remove elements, iterate backwards
                        for i in range(len(self.forbidden_calls) - 1, -1, -1):
                            func = self.forbidden_calls[i]
                            f = BinaryInfo.forbidden_functions[func]
                            if 'waiver_regex' not in f:
                                continue
                            r = f['waiver_regex'].search(line)
                            if r:
                                del self.forbidden_calls[i]

            if self.non_pic:
                self.non_pic = 'TEXTREL' in res[1]

            # Ignore all exit() calls if fork() is being called.
            # Does not have any context at all but without this kludge, the
            # number of false positives would probably be intolerable.
            if fork_called:
                self.exit_calls = []

            # check if chroot is near chdir (since otherwise, chroot is called
            # without chdir)
            if not BinaryInfo.objdump_call_regex and self.chroot and self.chdir:
                # On some architectures, e.g. PPC, it is to difficult to
                # find the actual invocations of chroot/chdir, if both
                # exist assume chroot is fine
                self.chroot_near_chdir = True

            elif self.chroot and self.chdir:
                p = subprocess.Popen(('objdump', '-d', path),
                                     stdout=subprocess.PIPE, bufsize=-1,
                                     env=dict(os.environ, LC_ALL="C"))
                with p.stdout:
                    index = 0
                    chroot_index = -99
                    chdir_index = -99
                    for line in p.stdout:
                        res = BinaryInfo.objdump_call_regex.search(line)
                        if not res:
                            continue
                        if b'@plt' not in res.group(1):
                            pass
                        elif b'chroot@plt' in res.group(1):
                            chroot_index = index
                            if abs(chroot_index - chdir_index) <= 2:
                                self.chroot_near_chdir = True
                                break
                        elif b'chdir@plt' in res.group(1):
                            chdir_index = index
                            if abs(chroot_index - chdir_index) <= 2:
                                self.chroot_near_chdir = True
                                break
                        index += 1
                if p.wait() and not self.chroot_near_chdir:
                    printWarning(pkg, 'binaryinfo-objdump-failed', fname)
                    self.chroot_near_chdir = True  # avoid false positive
                elif chroot_index == -99 and chdir_index == -99:
                    self.chroot_near_chdir = True  # avoid false positive

        else:
            self.readelf_error = True
            # Go and others are producing ar archives that don't have ELF
            # headers, so don't complain about it
            if not is_ar:
                printWarning(pkg, 'binaryinfo-readelf-failed',
                             fname, re.sub('\n.*', '', res[1]))

        try:
            with open(path, 'rb') as fobj:
                fobj.seek(-12, os.SEEK_END)
                self.tail = Pkg.b2s(fobj.read())
        except Exception as e:
            printWarning(pkg, 'binaryinfo-tail-failed %s: %s' % (fname, e))

        # Undefined symbol and unused direct dependency checks make sense only
        # for installed packages.
        # skip debuginfo: https://bugzilla.redhat.com/190599
        if not is_ar and not is_debug and isinstance(pkg, Pkg.InstalledPkg):
            # We could do this with objdump, but it's _much_ simpler with ldd.
            res = Pkg.getstatusoutput(('ldd', '-d', '-r', path))
            if not res[0]:
                for line in res[1].splitlines():
                    undef = BinaryInfo.undef_regex.search(line)
                    if undef:
                        self.undef.append(undef.group(1))
                if self.undef:
                    try:
                        res = Pkg.getstatusoutput(['c++filt'] + self.undef)
                        if not res[0]:
                            self.undef = res[1].splitlines()
                    except OSError:
                        pass
            else:
                printWarning(pkg, 'ldd-failed', fname)
            res = Pkg.getstatusoutput(('ldd', '-r', '-u', path))
            if res[0]:
                # Either ldd doesn't grok -u (added in glibc 2.3.4) or we have
                # unused direct dependencies
                in_unused = False
                for line in res[1].splitlines():
                    if not line.rstrip():
                        pass
                    elif line.startswith('Unused direct dependencies'):
                        in_unused = True
                    elif in_unused:
                        unused = BinaryInfo.unused_regex.search(line)
                        if unused:
                            self.unused.append(unused.group(1))
                        else:
                            in_unused = False


path_regex = re.compile(r'(.*/)([^/]+)')
numeric_dir_regex = re.compile(r'/usr(?:/share)/man/man./(.*)\.[0-9](?:\.gz|\.bz2)')
versioned_dir_regex = re.compile(r'[^.][0-9]')
ldso_soname_regex = re.compile(r'^ld(-linux(-(ia|x86_)64))?\.so')
so_regex = re.compile(r'/lib(64)?/[^/]+\.so(\.[0-9]+)*$')
validso_regex = re.compile(r'(\.so\.\d+(\.\d+)*|\d\.so)$')
sparc_regex = re.compile(r'SPARC32PLUS|SPARC V9|UltraSPARC')
system_lib_paths = Config.getOption('SystemLibPaths', DEFAULT_SYSTEM_LIB_PATHS)
pie_exec_re = Config.getOption('PieExecutables')
if pie_exec_re:
    pie_exec_re = re.compile(pie_exec_re)
usr_lib_regex = re.compile(r'^/usr/lib(64)?/')
bin_regex = re.compile(r'^(/usr(/X11R6)?)?/s?bin/')
soversion_regex = re.compile(r'.*?([0-9][.0-9]*)\\.so|.*\\.so\\.([0-9][.0-9]*).*')
reference_regex = re.compile(r'\.la$|^/usr/lib(64)?/pkgconfig/')
usr_lib_exception_regex = re.compile(Config.getOption('UsrLibBinaryException', r'^/usr/lib(64)?/(perl|python|ruby|menu|pkgconfig|ocaml|lib[^/]+\.(so|l?a)$|bonobo/servers/|\.build-id)'))
srcname_regex = re.compile(r'(.*?)-[0-9]')
invalid_dir_ref_regex = re.compile(r'/(home|tmp)(\W|$)')
ocaml_mixed_regex = re.compile(r'^Caml1999X0\d\d$')
usr_arch_share_regex = re.compile(r'/share/.*/(?:x86|i.86|x86_64|ppc|ppc64|s390|s390x|ia64|m68k|arm|aarch64|mips|riscv)')


def dir_base(path):
    res = path_regex.search(path)
    if res:
        return res.group(1), res.group(2)
    else:
        return '', path


class BinariesCheck(AbstractCheck.AbstractCheck):

    def __init__(self):
        AbstractCheck.AbstractCheck.__init__(self, 'BinariesCheck')

    def check_binary(self, pkg):
        files = pkg.files()
        exec_files = []
        has_lib = False
        version = None
        binary = False
        binary_in_usr_lib = False
        has_usr_lib_file = False
        file_in_lib64 = False

        multi_pkg = False
        srpm = pkg[rpm.RPMTAG_SOURCERPM]
        if srpm:
            res = srcname_regex.search(srpm)
            if res:
                multi_pkg = (pkg.name != res.group(1))

        for fname, pkgfile in files.items():

            if not stat.S_ISDIR(pkgfile.mode) and usr_lib_regex.search(fname):
                has_usr_lib_file = True
                if not binary_in_usr_lib and \
                        usr_lib_exception_regex.search(fname):
                    # Fake that we have binaries there to avoid
                    # only-non-binary-in-usr-lib false positives
                    binary_in_usr_lib = True

            if stat.S_ISREG(pkgfile.mode) and \
                    (fname.startswith("/usr/lib64") or fname.startswith("/lib64")):
                file_in_lib64 = True

            is_elf = pkgfile.magic.startswith('ELF ')
            is_ar = 'current ar archive' in pkgfile.magic
            is_ocaml_native = 'Objective caml native' in pkgfile.magic
            is_lua_bytecode = 'Lua bytecode' in pkgfile.magic
            is_shell = "shell script" in pkgfile.magic
            is_binary = is_elf or is_ar or is_ocaml_native or is_lua_bytecode

            if is_shell:
                with open(pkgfile.path, 'rb') as inputf:
                    if (b'This wrapper script should never '
                            b'be moved out of the build directory' in inputf.read(2048)):
                        printError(pkg, 'libtool-wrapper-in-package', fname)

            if not is_binary:
                if reference_regex.search(fname):
                    lines = pkg.grep(invalid_dir_ref_regex, fname)
                    if lines:
                        printError(pkg, 'invalid-directory-reference', fname,
                                   '(line %s)' % ", ".join(lines))
                continue

            # binary files only from here on

            binary = True

            if has_usr_lib_file and not binary_in_usr_lib and \
                    usr_lib_regex.search(fname):
                binary_in_usr_lib = True

            if pkg.arch == 'noarch':
                printError(
                    pkg,
                    'arch-independent-package-contains-binary-or-object',
                    fname)
                continue

            # arch dependent packages only from here on

            # in /usr/share ?
            if fname.startswith('/usr/share/') and not usr_arch_share_regex.search(fname):
                printError(pkg, 'arch-dependent-file-in-usr-share', fname)

            # in /etc ?
            if fname.startswith('/etc/'):
                printError(pkg, 'binary-in-etc', fname)

            if pkg.arch == 'sparc' and sparc_regex.search(pkgfile.magic):
                printError(pkg, 'non-sparc32-binary', fname)

            if is_ocaml_native or is_lua_bytecode or fname.endswith('.o') or \
                    fname.endswith('.static'):
                continue

            # stripped ?
            if 'not stripped' in pkgfile.magic:
                printWarning(pkg, 'unstripped-binary-or-object', fname)

            # inspect binary file
            is_shlib = so_regex.search(fname)
            bin_info = BinaryInfo(pkg, pkgfile.path, fname, is_ar, is_shlib)

            if is_shlib:
                has_lib = True

            # shared libs
            if is_shlib and not bin_info.readelf_error:

                # so name in library
                if not bin_info.soname:
                    printWarning(pkg, 'no-soname', fname)
                else:
                    if not validso_regex.search(bin_info.soname):
                        printError(pkg, 'invalid-soname', fname,
                                   bin_info.soname)
                    else:
                        (directory, base) = dir_base(fname)
                        try:
                            symlink = directory + bin_info.soname
                            link = files[symlink].linkto
                            if link not in (fname, base, ''):
                                printError(pkg, 'invalid-ldconfig-symlink',
                                           fname, link)
                        except KeyError:
                            if base.startswith("lib") or \
                               base.startswith("ld-"):
                                printError(pkg, 'no-ldconfig-symlink', fname)

                    res = soversion_regex.search(bin_info.soname)
                    if res:
                        soversion = res.group(1) or res.group(2)
                        if version is None:
                            version = soversion
                        elif version != soversion:
                            version = -1

                if bin_info.non_pic:
                    printError(pkg, 'shlib-with-non-pic-code', fname)

                # It could be useful to check these for others than shared
                # libs only, but that has potential to generate lots of
                # false positives and noise.
                for s in bin_info.undef:
                    printWarning(pkg, 'undefined-non-weak-symbol', fname, s)
                for s in bin_info.unused:
                    printWarning(pkg, 'unused-direct-shlib-dependency',
                                 fname, s)

                # calls exit() or _exit()?
                for ec in bin_info.exit_calls:
                    printWarning(pkg, 'shared-lib-calls-exit', fname, ec)

            for ec in bin_info.forbidden_calls:
                printWarning(pkg, ec, fname,
                             BinaryInfo.forbidden_functions[ec]['f_name'])

            # rpath ?
            if bin_info.rpath:
                for p in bin_info.rpath:
                    if p in system_lib_paths or not usr_lib_regex.search(p):
                        printError(pkg, 'binary-or-shlib-defines-rpath',
                                   fname, bin_info.rpath)
                        break

            is_exec = 'executable' in pkgfile.magic
            is_shobj = 'shared object' in pkgfile.magic
            is_pie_exec = 'pie executable' in pkgfile.magic

            if not is_exec and not is_shobj:
                continue

            if is_shobj and not is_exec and '.so' not in fname and \
                    bin_regex.search(fname):
                # pkgfile.magic does not contain "executable" for PIEs
                is_exec = True

            if is_exec:

                if bin_regex.search(fname):
                    exec_files.append(fname)

                if ocaml_mixed_regex.search(bin_info.tail):
                    printWarning(pkg, 'ocaml-mixed-executable', fname)

                if ((not is_shobj and not is_pie_exec) and
                        pie_exec_re and pie_exec_re.search(fname)):
                    printError(pkg, 'non-position-independent-executable',
                               fname)

            if bin_info.readelf_error:
                continue

            if not bin_info.needed and not (
                    bin_info.soname and
                    ldso_soname_regex.search(bin_info.soname)):
                if is_shobj:
                    printError(pkg,
                               'shared-lib-without-dependency-information',
                               fname)
                else:
                    printError(pkg, 'statically-linked-binary', fname)

            else:
                # linked against libc ?
                if "libc." not in fname and \
                   (not bin_info.soname or
                    ("libc." not in bin_info.soname and
                     not ldso_soname_regex.search(bin_info.soname))):

                    found_libc = False
                    for lib in bin_info.needed:
                        if "libc." in lib:
                            found_libc = True
                            break

                    if not found_libc:
                        if is_shobj:
                            printError(pkg, 'library-not-linked-against-libc',
                                       fname)
                        else:
                            printError(pkg, 'program-not-linked-against-libc',
                                       fname)

            if bin_info.stack:
                if bin_info.exec_stack:
                    printWarning(pkg, 'executable-stack', fname)
            elif not bin_info.readelf_error and (
                    pkg.arch.endswith("86") or
                    pkg.arch.startswith("pentium") or
                    pkg.arch in ("athlon", "x86_64")):
                printError(pkg, 'missing-PT_GNU_STACK-section', fname)

            if bin_info.setgid and bin_info.setuid and not bin_info.setgroups:
                printError(pkg, 'missing-call-to-setgroups-before-setuid',
                           fname)

            if bin_info.chroot and not bin_info.chroot_near_chdir:
                printError(pkg, 'missing-call-to-chdir-with-chroot', fname)

            if bin_info.mktemp:
                printError(pkg, 'call-to-mktemp', fname)

        if has_lib:
            for f in exec_files:
                printError(pkg, 'executable-in-library-package', f)
            for f in files:
                res = numeric_dir_regex.search(f)
                fn = res and res.group(1) or f
                if f not in exec_files and not so_regex.search(f) and \
                        not versioned_dir_regex.search(fn):
                    printError(pkg, 'non-versioned-file-in-library-package', f)
            if version and version != -1 and version not in pkg.name:
                printError(pkg, 'incoherent-version-in-name', version)

        if not binary and not multi_pkg and not file_in_lib64 and pkg.arch != 'noarch':
            printError(pkg, 'no-binary')

        if pkg.arch == 'noarch' and file_in_lib64:
            printError(pkg, 'noarch-with-lib64')

        if has_usr_lib_file and not binary_in_usr_lib:
            printWarning(pkg, 'only-non-binary-in-usr-lib')


# Create an object to enable the auto registration of the test
check = BinariesCheck()

# Add information about checks
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

'noarch-with-lib64',
'''This package is marked as noarch but installs files into lib64.
Not all architectures have this in path, so the package can't be
noarch.''',

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
Use the ``eu-findtextrel'' command on a library with debugging symbols
to list code compiled without -fPIC.

Another common mistake that causes this problem is linking with
``gcc -Wl,-shared'' instead of ``gcc -shared''.''',

'libtool-wrapper-in-package',
'''Your package contains a libtool wrapper shell script. This
will not work. Instead of installing the libtool wrapper file run
``libtool --mode=install install -m perm <file> <dest>'' in order
to install the relinked file.''',

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

# http://www.redhat.com/archives/fedora-maintainers/2006-June/msg00176.html
'unused-direct-shlib-dependency',
'''The binary contains unused direct shared library dependencies.  This may
indicate gratuitously bloated linkage; check that the binary has been linked
with the intended shared libraries only.''',

'only-non-binary-in-usr-lib',
'''There are only non binary files in /usr/lib so they should be in
/usr/share.''',

'binaryinfo-readelf-failed',
'''Executing readelf on this file failed, all checks could not be run.''',

'binaryinfo-objdump-failed',
'''Executing objdump on this file failed, all checks could not be run.''',

'binaryinfo-tail-failed',
'''Reading trailing bytes of this file failed, all checks could not be run.''',

'ldd-failed',
'''Executing ldd on this file failed, all checks could not be run.''',

'executable-stack',
'''The binary declares the stack as executable.  Executable stack is usually an
error as it is only needed if the code contains GCC trampolines or similar
constructs which uses code on the stack.  One common source for needlessly
executable stack cases are object files built from assembler files which
don\'t define a proper .note.GNU-stack section.''',

'missing-PT_GNU_STACK-section',
'''The binary lacks a PT_GNU_STACK section.  This forces the dynamic linker to
make the stack executable.  Usual suspects include use of a non-GNU linker or
an old GNU linker version.''',

'shared-lib-calls-exit',
'''This library package calls exit() or _exit(), probably in a non-fork()
context. Doing so from a library is strongly discouraged - when a library
function calls exit(), it prevents the calling program from handling the
error, reporting it to the user, closing files properly, and cleaning up any
state that the program has. It is preferred for the library to return an
actual error code and let the calling program decide how to handle the
situation.''',

'ocaml-mixed-executable',
'''Executables built with ocamlc -custom are deprecated.  Packagers should ask
upstream maintainers to build these executables without the -custom option.  If
this cannot be changed and the executable needs to be packaged in its current
form, make sure that rpmbuild does not strip it during the build, and on setups
that use prelink, make sure that prelink does not strip it either, usually by
placing a blacklist file in /etc/prelink.conf.d.  For more information, see
http://bugs.debian.org/cgi-bin/bugreport.cgi?bug=256900#49''',

'non-position-independent-executable',
'''This executable must be position independent.  Check that it is built with
-fPIE/-fpie in compiler flags and -pie in linker flags.''',

'missing-call-to-setgroups-before-setuid',
'''This executable is calling setuid and setgid without setgroups or
initgroups. There is a high probability this means it didn't relinquish all
groups, and this would be a potential security issue to be fixed. Seek POS36-C
on the web for details about the problem.''',

'missing-call-to-chdir-with-chroot',
'''This executable appears to call chroot without using chdir to change the
current directory. This is likely an error and permits an attacker to break out
of the chroot by using fchdir. While that's not always a security issue, this
has to be checked.''',

'call-to-mktemp',
'''This executable calls mktemp. As advised by the manpage (mktemp(3)), this
function should be avoided. Some implementations are deeply insecure, and there
is a race condition between the time of check and time of use (TOCTOU).
See http://capec.mitre.org/data/definitions/29.html for details, and contact
upstream to have this issue fixed.''',

'unstripped-binary-or-object',
'''This executable should be stripped from debugging symbols, in order to take
less space and be loaded faster. This is usually done automatically at
buildtime by rpm. Check the build logs and the permission on the file (some
implementations only strip if the permission is 0755).'''
)

# BinariesCheck.py ends here
