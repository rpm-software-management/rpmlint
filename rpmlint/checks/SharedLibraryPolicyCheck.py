import os
import re
import rpm
import stat

from rpmlint.checks.AbstractCheck import AbstractCheck
from rpmlint import Pkg


class LibraryPolicyCheck(AbstractCheck.AbstractCheck):
    """
    Verify shared library packaging policy rules

    This package validates the shared libraries naming scheme based
    on the Debian/openSUSE shared libraries policy:
     https://en.opensuse.org/openSUSE:Shared_library_packaging_policy
     https://www.debian.org/doc/debian-policy/ch-sharedlibs.html
    """
    re_soname_strongly_versioned = re.compile(r'-[\d\.]+\.so$')
    # the pkgname is based on soname if ending with number; special option is flavor build
    re_soname_pkg = re.compile(r'^lib\S+(\d+(-(32|64)bit)?)$')
    re_so_files = re.compile(r'\S+.so((.(\d+))+)?$')

    def check(self, pkg):
        if pkg.is_source:
            return

        # we don't care about develpkgs
        if pkg.name.endswith('-devel'):
            return

        # check the pkg has any libname
        libfiles = []
        for fname, pkgfile in pkg.files.items():
            if not self.re_so_files.match(fname):
                continue
            libfiles += fname

        # if we didn't find any library files then we
        # don't need to check anything
        if not libfiles:
            # verify if name does not match the slpp and if we still don't have any lib then error out
            if self.re_soname_pkg.match(pkg.name):
                self.output.add_info('E', pkg, 'shlib-policy-missing-lib')
            return

        # the soname validation matching the name is done
        # already in BinaryCheck._check_shared_library
        
        # Search for shared libraries in this package
        libs = set()
        libs_needed = set()
        libs_to_dir = dict()
        dirs = set()
        reqlibs = set()
        pkg_requires = [x.name for x in pkg.requires]

        for f, pkgfile in files.items():
            if '.so.' in f or f.endswith('.so'):
                filename = pkg.dirName() + '/' + f
                if stat.S_ISREG(files[f].mode) and pkgfile.magic.startswith('ELF '):
                    bi = BinaryInfo(pkg, filename, f, False, True)
                    libs_needed = libs_needed.union(bi.needed)
                    if bi.soname != 0:
                        lib_dir = '/'.join(f.split('/')[:-1])
                        libs.add(bi.soname)
                        libs_to_dir[bi.soname] = lib_dir
                        dirs.add(lib_dir)
                    if bi.soname in pkg_requires:
                        # But not if the library is used by the pkg itself
                        # This avoids program packages with their own
                        # private lib
                        # FIXME: we'd need to check if somebody else links
                        # to this lib
                        reqlibs.add(bi.soname)

        # If this is a program package (all libs it provides are
        # required by itself), bail out
        if not pkg.name.startswith('lib') and len(libs.difference(reqlibs)) == 0:
            return

        std_lib_package = False
        if pkg.name.startswith('lib') and pkg.name[-1].isdigit():
            std_lib_package = True

        # ignore libs in a versioned non_std_dir
        if std_lib_package:
            for lib in libs.copy():
                lib_dir = libs_to_dir[lib]
                for lib_part in lib_dir.split('/'):
                    if len(lib_part) == 0:
                        continue
                    if lib_part[-1].isdigit() and not lib_part.endswith('lib64'):
                        libs.remove(lib)
                        break

        # Check for non-versioned libs in a std lib package
        if std_lib_package:
            for lib in libs.copy():
                if (not (lib[-1].isdigit() or
                         self.strongly_versioned_re.search(lib))):
                    self.output.add_info('W', pkg, 'shlib-unversioned-lib', lib)

        # Verify no non-lib stuff is in the package
        dirs = set()
        for f in files:
            if os.path.isdir(pkg.dirName() + f):
                dirs.add(f)

        # Verify shared lib policy package doesn't have hard dependency on non-lib packages
        if std_lib_package:
            for dep in pkg.requires():
                if (dep[0].startswith('rpmlib(') or dep[0].startswith('config(')):
                    continue
                if (dep[1] & (rpm.RPMSENSE_GREATER | rpm.RPMSENSE_EQUAL)) == rpm.RPMSENSE_EQUAL:
                    self.output.add_info('W', pkg, 'shlib-fixed-dependency', Pkg.formatRequire(dep[0], dep[1], dep[2]))

        # Verify non-lib stuff does not add dependencies
        if libs:
            for dep in pkg_requires.difference(_essential_dependencies):
                if '.so.' in dep and dep not in libs and dep not in libs_needed:
                    self.output.add_info('E', pkg, 'shlib-policy-excessive-dependency', dep)

        # Check for non-versioned directories beyond sysdirs in package
        sysdirs = ('/lib', '/lib64', '/usr/lib', '/usr/lib64',
                   '/usr/share', '/usr/share/licenses',
                   '/usr/share/doc/packages')
        cdirs = set()
        for sysdir in sysdirs:
            done = set()
            for dir in dirs:
                if dir.startswith(sysdir + '/'):
                    ssdir = str.split(dir[len(sysdir) + 1:], '/')[0]
                    if not ssdir[-1].isdigit():
                        cdirs.add(sysdir + '/' + ssdir)
                    done.add(dir)
            dirs = dirs.difference(done)
        map(lambda dir: self.output.add_info('E', pkg, 'shlib-policy-nonversioned-dir', dir), cdirs)
