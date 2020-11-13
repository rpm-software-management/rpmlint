from pathlib import Path
import re
import stat

import rpm
from rpmlint.checks.AbstractCheck import AbstractCheck
from rpmlint.pkg import formatRequire
from rpmlint.readelfparser import ReadelfParser


class SharedLibraryPolicyCheck(AbstractCheck):
    """
    Verify shared library packaging policy rules

    This package validates the shared libraries naming scheme based
    on the Debian/openSUSE shared libraries policy:
     https://en.opensuse.org/openSUSE:Shared_library_packaging_policy
     https://www.debian.org/doc/debian-policy/ch-sharedlibs.html
    """

    def __init__(self, config, output):
        super().__init__(config, output)
        self.re_soname_strongly_versioned = re.compile(r'-[\d\.]+\.so$')
        # the pkgname is based on soname if ending with number; special option is flavor build
        self.re_soname_pkg = re.compile(r'^lib\S+(\d+(-(32|64)bit)?)$')
        self.re_so_files = re.compile(r'\S+.so((.(\d+))+)?$')

    def _check_missing_policy_lib(self, pkg):
        # check the pkg has any libname
        libfiles = []
        for fname in pkg.files.keys():
            if not self.re_so_files.match(fname):
                continue
            libfiles.append(fname)

        # if we didn't find any library files then we
        # don't need to check anything
        if not libfiles:
            # verify if name does not match the slpp and if we still don't have any lib then error out
            if self.re_soname_pkg.match(pkg.name):
                self.output.add_info('E', pkg, 'shlib-policy-missing-lib')

    def check(self, pkg):
        if pkg.is_source:
            return

        # Consider only non-development, non-language library packages
        if (not pkg.name.startswith('lib') or
                pkg.name.endswith('-devel') or
                pkg.name.endswith('-lang')):
            return

        self._check_missing_policy_lib(pkg)

        # the soname validation matching the name is done
        # already in BinaryCheck._check_shared_library
        # Search for shared libraries in this package
        libs = set()
        libs_needed = set()
        libs_to_dir = {}
        reqlibs = set()
        pkg_requires = {x.name.split('(')[0] for x in pkg.requires}

        for filename, pkgfile in pkg.files.items():
            path = Path(filename)
            if '.so.' in filename or filename.endswith('.so'):
                if stat.S_ISREG(pkg.files[filename].mode) and pkgfile.magic.startswith('ELF '):
                    readelf_parser = ReadelfParser(pkgfile.path, filename)
                    failed_reason = readelf_parser.parsing_failed_reason()
                    if failed_reason:
                        self.output.add_info('E', pkg, 'readelf-failed', filename, failed_reason)
                        return
                    dyn_section = readelf_parser.dynamic_section_info
                    libs_needed = libs_needed.union(dyn_section.needed)
                    if dyn_section.soname:
                        lib_dir = str(path.parent)
                        libs.add(dyn_section.soname)
                        libs_to_dir[dyn_section.soname] = lib_dir
                    if dyn_section.soname in pkg_requires:
                        # But not if the library is used by the pkg itself
                        # This avoids program packages with their own
                        # private lib
                        # FIXME: we'd need to check if somebody else links
                        # to this lib
                        reqlibs.add(dyn_section.soname)

        if not libs.difference(reqlibs):
            return

        if pkg.name[-1].isdigit():
            # ignore libs in a versioned non_std_dir
            for lib in libs.copy():
                lib_dir = libs_to_dir[lib]
                for lib_part in lib_dir.split('/'):
                    if not lib_part:
                        continue
                    if lib_part[-1].isdigit() and not lib_part.endswith('lib64'):
                        libs.remove(lib)
                        break

            # Check for non-versioned libs in a std lib package
            for lib in libs.copy():
                if (not (lib[-1].isdigit() or
                         self.re_soname_strongly_versioned.search(lib))):
                    self.output.add_info('W', pkg, 'shlib-unversioned-lib', lib)

            # Verify shared lib policy package doesn't have hard dependency on non-lib packages
            for dep in pkg.requires:
                if dep[0].startswith('rpmlib(') or dep[0].startswith('config('):
                    continue
                if (dep[1] & (rpm.RPMSENSE_GREATER | rpm.RPMSENSE_EQUAL)) == rpm.RPMSENSE_EQUAL:
                    self.output.add_info('W', pkg, 'shlib-fixed-dependency', formatRequire(dep[0], dep[1], dep[2]))

        # Verify non-lib stuff does not add dependencies
        if libs:
            for dep in pkg_requires:
                if '.so.' in dep and dep not in libs and dep not in libs_needed:
                    self.output.add_info('E', pkg, 'shlib-policy-excessive-dependency', dep)

        # FIXME: implement (#567)
        # Check if the files/folders are unversioned in the library package.
        # In general you can't co-install the soname packages if they all provide some datafiles
        # or configuration files.
        # When testing one of examples is libsemanage1:
        #   /etc/selinux
        #   /etc/selinux/semanage.conf
        #   /usr/lib64/libsemanage.so.1
        # The above would be fine if the semanage.conf would be update-alternatived, or suffixed
        # but if someone introduces libsemanage2 they can't be installed both at once.
