import concurrent.futures
from pathlib import Path
import re
import stat

import rpm
from rpmlint.arparser import ArParser
from rpmlint.checks.AbstractCheck import AbstractCheck
from rpmlint.lddparser import LddParser
from rpmlint.objdumpparser import ObjdumpParser
from rpmlint.pkg import FakePkg, InstalledPkg
from rpmlint.readelfparser import ReadelfParser
from rpmlint.stringsparser import StringsParser


class BinariesCheck(AbstractCheck):
    """
    Checks for binary files in the package.
    """
    srcname_regex = re.compile(r'(.*?)-[0-9]')
    validso_regex = re.compile(r'(\.so\.\d+(\.\d+)*|\d\.so)$')
    soversion_regex = re.compile(r'.*?([0-9][.0-9]*)\.so|.*\.so\.([0-9][.0-9]*).*')
    usr_lib_regex = re.compile(r'^/usr/lib(64)?/')
    ldso_soname_regex = re.compile(r'^ld(-linux(-(ia|x86_)64))?\.so')

    numeric_dir_regex = re.compile(r'/usr(?:/share)/man/man./(.*)\.[0-9](?:\.gz|\.bz2)')
    versioned_dir_regex = re.compile(r'[^.][0-9]')
    so_regex = re.compile(r'/lib(64)?/[^/]+\.so(\.[0-9]+)*$')
    bin_regex = re.compile(r'^(/usr(/X11R6)?)?/s?bin/')
    la_file_regex = re.compile(r'\.la$')
    invalid_dir_ref_regex = re.compile(r'/(home|tmp)(\W|$)')
    usr_arch_share_regex = re.compile(r'/share/.*/(?:x86|i.86|x86_64|ppc|ppc64|s390|s390x|ia64|m68k|arm|aarch64|mips|riscv)')

    def __init__(self, config, output):
        super().__init__(config, output)
        self.checked_files = 0
        self.system_lib_paths = config.configuration['SystemLibPaths']
        self.pie_exec_regex_list = []
        for regex in config.configuration['PieExecutables']:
            self.pie_exec_regex_list.append(re.compile(regex))
        self.usr_lib_exception_regex = re.compile(config.configuration['UsrLibBinaryException'])

        self.setgid_call_regex = self.create_regexp_call(r'set(?:res|e)?gid')
        self.setuid_call_regex = self.create_regexp_call(r'set(?:res|e)?uid')
        self.setgroups_call_regex = self.create_regexp_call(r'(?:ini|se)tgroups')
        self.mktemp_call_regex = self.create_regexp_call('mktemp')
        self.gethostbyname_call_regex = self.create_regexp_call(r'(gethostbyname|gethostbyname2|gethostbyaddr|gethostbyname_r|gethostbyname2_r|gethostbyaddr_r)')

        # register all check functions
        self.check_functions = [self._check_lto_section,
                                self._check_no_text_in_archive,
                                self._check_missing_symtab_in_archive,
                                self._check_missing_debug_info_in_archive,
                                self._check_executable_stack,
                                self._check_shared_library,
                                self._check_dependency,
                                self._check_library_dependency_location,
                                self._check_security_functions,
                                self._check_rpath,
                                self._check_library_dependency,
                                self._check_forbidden_functions,
                                self._check_executable_shlib,
                                self._check_optflags]

    @staticmethod
    def create_nonlibc_regexp_call(call):
        r = r'(%s)\s?.*$' % call
        return re.compile(r)

    @staticmethod
    def create_regexp_call(call):
        r = r'(%s(?:@GLIBC\S+)?)(?:\s|$)' % call
        return re.compile(r)

    def _check_libtool_wrapper(self, pkg, fname, pkgfile):
        """
        Print an error if the fname file contains a libtool wrapper shell
        script.
        """
        if 'shell script' in pkgfile.magic:
            file_start = None
            try:
                with open(pkgfile.path, 'rb') as inputf:
                    file_start = inputf.read(2048)
            except IOError:
                pass
            if (file_start and b'This wrapper script should never '
                               b'be moved out of the build directory'
                    in file_start):
                self.output.add_info('E', pkg, 'libtool-wrapper-in-package',
                                     fname)

    def _check_invalid_la_file(self, pkg, fname):
        """
        Check if the fname is an .la file and contains a reference to the
        invalid directories ('/tmp' or '/home').

        If so then print a corresponding error with the matching line numbers.
        """
        if self.la_file_regex.search(fname):
            lines = pkg.grep(self.invalid_dir_ref_regex, fname)
            if lines:
                self.output.add_info('E', pkg, 'invalid-la-file', fname,
                                     '(line %s)' % ', '.join(lines))

    def _check_binary_in_noarch(self, pkg, bin_name):
        """
        Print an error if the binary file bin_name is in the noarch package.
        """
        if pkg.arch == 'noarch':
            self.output.add_info('E', pkg,
                                 'arch-independent-package-contains-binary-or-object',
                                 bin_name)

    def _check_binary_in_usr_share(self, pkg, bin_name):
        """
        Print an error if binary file bin_name is installed in /usr/share.

        We suppose that the package is arch dependent.
        """
        if bin_name.startswith('/usr/share/') and \
                not self.usr_arch_share_regex.search(bin_name):
            self.output.add_info('E', pkg, 'arch-dependent-file-in-usr-share',
                                 bin_name)

    def _check_binary_in_etc(self, pkg, bin_name):
        """
        Print an error if binary file bin_name is installed in /etc directory.

        We suppose that the package is arch dependent.
        """
        if bin_name.startswith('/etc/'):
            self.output.add_info('E', pkg, 'binary-in-etc', bin_name)

    def _check_unstripped_binary(self, bin_name, pkg, pkgfile):
        """
        Print a warning if the bin_name binary has unstripped debug symbols.

        We suppose that the package is arch dependent and bin_name is not
        ocaml native, lua bytecode, .o or .static.
        """
        if 'not stripped' in pkgfile.magic:
            self.output.add_info('W', pkg, 'unstripped-binary-or-object',
                                 bin_name)

    def _check_non_pie(self, pkg, bin_name):
        """
        Check if the bin_name binary is built with PIE.

        Print an error message if it's not while PIE is forced in
        configuration. Print a warning if it's not forced.
        We suppose that the package is arch dependent and bin_name is binary
        executable.
        """
        if not self.is_shobj and not self.is_pie_exec:
            if any(regex.search(bin_name) for regex in self.pie_exec_regex_list):
                self.output.add_info('E', pkg,
                                     'non-position-independent-executable',
                                     bin_name)
            else:
                self.output.add_info('W', pkg,
                                     'position-independent-executable-suggested',
                                     bin_name)

    def _check_exec_in_library(self, pkg, has_lib, exec_files):
        """
        Check if the library package has an executable file installed.

        Print an error for every such file.
        """
        if has_lib:
            for f in exec_files:
                self.output.add_info('E', pkg, 'executable-in-library-package', f)

    def _check_non_versioned(self, pkg, has_lib, exec_files):
        """
        Check if the library package contains library files in non-versioned
        directories.

        Print an error for every such file.
        """
        if has_lib:
            for f in pkg.files:
                res = self.numeric_dir_regex.search(f)
                fn = res and res.group(1) or f
                if f not in exec_files and not self.so_regex.search(f) and \
                        not self.versioned_dir_regex.search(fn):
                    self.output.add_info('E', pkg, 'non-versioned-file-in-library-package', f)

    def _check_no_binary(self, pkg, has_binary, multi_pkg, has_file_in_lib64):
        """
        Check if the arch dependent package contains any binaries.

        Print an error if there is no binary and it's not noarch.
        """
        if not has_binary and not multi_pkg and not has_file_in_lib64 and \
                pkg.arch != 'noarch':
            self.output.add_info('E', pkg, 'no-binary')

    def _check_noarch_with_lib64(self, pkg, has_file_in_lib64):
        """
        Print an error if we have a noarch package that contains a file
        in /usr/lib64.
        """
        if pkg.arch == 'noarch' and has_file_in_lib64:
            self.output.add_info('E', pkg, 'noarch-with-lib64')

    def _check_only_non_binary_in_usrlib(self, pkg, has_usr_lib_file, has_binary_in_usr_lib):
        """
        Check and print a warning if we have _only_ non-binary files in the
        '/usr/lib'.

        Note: non-binaries allowed via UsrLibBinaryException config option
        are considered binaries.
        """
        if has_usr_lib_file and not has_binary_in_usr_lib:
            self.output.add_info('W', pkg, 'only-non-binary-in-usr-lib')

    def _check_no_text_in_archive(self, pkg, pkgfile_path, path):
        """
        For an archive, test if any .text sections is non-empty.
        """
        if self.is_archive:
            for comment in self.readelf_parser.comment_section_info.comments:
                if comment.startswith('GHC '):
                    return

            for elf_file in self.readelf_parser.section_info.elf_files:
                for section in elf_file:
                    sn = section.name
                    if ((sn == '.preinit_array' or sn == '.init_array' or
                         sn == '.fini_array' or sn.startswith('.text') or
                         sn.startswith('.data')) and
                            section.size > 0):
                        return
            self.output.add_info('E', pkg, 'lto-no-text-in-archive', path)
            return

    def _check_missing_symtab_in_archive(self, pkg, pkgfile_path, path):
        """
        FIXME Add test coverage.
        """
        if self.is_archive:
            for elf_file in self.readelf_parser.section_info.elf_files:
                for section in elf_file:
                    if section.name == '.symtab':
                        return

            self.output.add_info('E', pkg, 'static-library-without-symtab', path)

    def _check_missing_debug_info_in_archive(self, pkg, pkgfile_path, path):
        if self.is_archive:
            for elf_file in self.readelf_parser.section_info.elf_files:
                for section in elf_file:
                    if section.name.startswith('.debug_'):
                        return
            self.output.add_info('E', pkg, 'static-library-without-debuginfo', path)

    # Check for LTO sections
    def _check_lto_section(self, pkg, pkgfile_path, path):
        for elf_file in self.readelf_parser.section_info.elf_files:
            for section in elf_file:
                if '.gnu.lto_.' in section.name:
                    self.output.add_info('E', pkg, 'lto-bytecode', path)
                    return

    def _check_executable_stack(self, pkg, pkgfile_path, path):
        """
        Check if the stack is declared as executable which is usually an error.

        FIXME Add test coverage.
        """

        # Do not check kernel modules and archives
        if not self.is_archive and not path.startswith('/lib/modules/'):
            stack_headers = [h for h in self.readelf_parser.program_header_info.headers if h.name == 'GNU_STACK']
            if not stack_headers:
                self.output.add_info('E', pkg, 'missing-PT_GNU_STACK-section', path)
            elif 'E' in stack_headers[0].flags:
                self.output.add_info('E', pkg, 'executable-stack', path)

    def _check_soname_symlink(self, pkg, shlib, soname):
        """
        Check that we have a symlink with the soname in the package and it
        points to the checked shared library.

        Print an error if the symlink is invalid or missing.
        """
        path = Path(shlib)
        symlink = path.parent / soname
        try:

            link = pkg.files[str(symlink)].linkto
            if link not in (shlib, path.parent, ''):
                self.output.add_info('E', pkg, 'invalid-ldconfig-symlink', shlib, link)
        except KeyError:
            # if we do not have a symlink, report an issue
            if path.name.startswith('lib') or path.name.startswith('ld-'):
                self.output.add_info('E', pkg, 'no-ldconfig-symlink', shlib)

    def _check_shared_library(self, pkg, pkgfile_path, path):
        """
        Various checks for the shared library.

        1) Print 'no-soname' warning it the library has no soname present.
        2) Print 'invalid-soname' error if the soname is not valid.
        3) Print 'shlib-policy-name-error' error when the library major
           version is not present in the package name.
        4) Print 'shlib-with-non-pic-code' error if the library contains
           object code that was compiled without -fPIC.
        """
        if not self.readelf_parser.is_shlib:
            return

        soname = self.readelf_parser.dynamic_section_info.soname
        if not soname:
            self.output.add_info('W', pkg, 'no-soname', path)
        else:
            if not self.validso_regex.search(soname):
                self.output.add_info('E', pkg, 'invalid-soname', path, soname)
            else:
                self._check_soname_symlink(pkg, path, soname)

                # check if the major version of the library is in the package
                # name
                res = self.soversion_regex.search(soname)
                if res:
                    soversion = res.group(1) or res.group(2)
                    if soversion and soversion not in pkg.name:
                        self.output.add_info('E', pkg, 'shlib-policy-name-error', soversion)

        # check if the object code in the library is compiled with PIC
        if self.readelf_parser.dynamic_section_info['TEXTREL']:
            self.output.add_info('E', pkg, 'shlib-with-non-pic-code', path)

    def _check_dependency(self, pkg, pkgfile_path, path):
        """
        FIXME Add test coverage.
        """
        # Undefined symbol and unused direct dependency checks make sense only
        # for installed packages.
        # skip debuginfo: https://bugzilla.redhat.com/190599
        #
        # following issues are errors for shared libs and warnings for executables
        if not self.is_dynamically_linked:
            return
        if not self.is_archive and not self.readelf_parser.is_debug:
            info_type = 'E' if self.readelf_parser.is_shlib else 'W'
            for symbol in self.ldd_parser.undefined_symbols:
                self.output.add_info(info_type, pkg, 'undefined-non-weak-symbol', path, symbol)
            for dependency in self.ldd_parser.unused_dependencies:
                self.output.add_info(info_type, pkg, 'unused-direct-shlib-dependency',
                                     path, dependency)

    def _check_library_dependency_location(self, pkg, pkgfile_path, path):
        """
        FIXME Add test coverage.
        """
        if not self.is_dynamically_linked:
            return

        if not self.is_archive:
            for dependency in self.ldd_parser.dependencies:
                if dependency.startswith('/opt/'):
                    self.output.add_info('E', pkg, 'linked-against-opt-library', path, dependency)
                    break

        nonusr = ('/bin', '/lib', '/sbin')
        if path.startswith(nonusr):
            for dependency in self.ldd_parser.dependencies:
                if dependency.startswith('/usr/'):
                    self.output.add_info('W', pkg, 'linked-against-usr-library', path, dependency)
                    break

    def _check_security_functions(self, pkg, pkgfile_path, path):
        setgid = any(self.readelf_parser.symbol_table_info.get_functions_for_regex(self.setgid_call_regex))
        setuid = any(self.readelf_parser.symbol_table_info.get_functions_for_regex(self.setuid_call_regex))
        setgroups = any(self.readelf_parser.symbol_table_info.get_functions_for_regex(self.setgroups_call_regex))
        mktemp = any(self.readelf_parser.symbol_table_info.get_functions_for_regex(self.mktemp_call_regex))
        gethostbyname = any(self.readelf_parser.symbol_table_info.get_functions_for_regex(self.gethostbyname_call_regex))

        if setgid and setuid and not setgroups:
            self.output.add_info('E', pkg, 'missing-call-to-setgroups-before-setuid', path)

        if mktemp:
            self.output.add_info('E', pkg, 'call-to-mktemp', path)

        if gethostbyname:
            self.output.add_info('W', pkg, 'binary-or-shlib-calls-gethostbyname', path)

    def _check_rpath(self, pkg, pkgfile_path, path):
        for runpath in self.readelf_parser.dynamic_section_info.runpath:
            if runpath in self.system_lib_paths or not self.usr_lib_regex.search(runpath):
                self.output.add_info('E', pkg, 'binary-or-shlib-defines-rpath', path, runpath)
                return

    def _check_library_dependency(self, pkg, pkgfile_path, path):
        if self.is_archive:
            return
        if path.startswith('/lib/modules/'):
            return

        dyn_section = self.readelf_parser.dynamic_section_info
        if not len(dyn_section.needed) and not (dyn_section.soname and
                                                self.ldso_soname_regex.search(dyn_section.soname)):
            if self.is_shobj:
                msg = 'shared-library-without-dependency-information'
            else:
                msg = 'statically-linked-binary'
            self.output.add_info('E', pkg, msg, path)
        else:
            # linked against libc ?
            if 'libc.' not in dyn_section.runpath and \
               (not dyn_section.soname or
                ('libc.' not in dyn_section.soname and
                 not self.ldso_soname_regex.search(dyn_section.soname))):
                for lib in dyn_section.needed:
                    if 'libc.' in lib:
                        return
                if self.is_shobj:
                    msg = 'library-not-linked-against-libc'
                else:
                    msg = 'program-not-linked-against-libc'
                self.output.add_info('W', pkg, msg, path)

    def _check_forbidden_functions(self, pkg, pkgfile_path, path):
        forbidden_functions = self.config.configuration['WarnOnFunction']
        if forbidden_functions:
            for name, func in forbidden_functions.items():
                # precompile regexps
                f_name = func['f_name']
                func['f_regex'] = self.create_nonlibc_regexp_call(f_name)
                if 'good_param' in func and func['good_param']:
                    func['waiver_regex'] = re.compile(func['good_param'])
                # register descriptions
                self.output.error_details.update({name: func['description']})

        forbidden_calls = []
        for r_name, func in forbidden_functions.items():
            if any(self.readelf_parser.symbol_table_info.get_functions_for_regex(func['f_regex'])):
                forbidden_calls.append(r_name)

        if not forbidden_calls:
            return

        strings_parser = StringsParser(pkgfile_path)
        failed_reason = strings_parser.parsing_failed_reason
        if failed_reason:
            self.output.add_info('E', pkg, 'strings-failed', path, failed_reason)
            return

        forbidden_functions_filtered = []

        for fn in forbidden_calls:
            f = forbidden_functions[fn]
            if 'waiver_regex' not in f:
                forbidden_functions_filtered.append(fn)
                continue

            waiver = any(map(lambda string: f['waiver_regex'].search(string), strings_parser.strings))
            if not waiver:
                forbidden_functions_filtered.append(fn)

        for fn in forbidden_functions_filtered:
            self.output.add_info('W', pkg, fn, path, forbidden_functions[fn]['f_name'])

    def _check_executable_shlib(self, pkg, pkgfile_path, path):
        if not self.is_exec and self.readelf_parser.is_shlib:
            interp = [h for h in self.readelf_parser.program_header_info.headers if h.name == 'INTERP']
            if interp:
                self.output.add_info('E', pkg, 'shared-library-not-executable', path)

    def _check_optflags(self, pkg, pkgfile_path, path):
        if self.is_archive:
            return

        mandatory_optflags = self.config.configuration['MandatoryOptflags']
        forbidden_optflags = self.config.configuration['ForbiddenOptflags']
        if not mandatory_optflags and not forbidden_optflags:
            return

        for dwarf_unit in self.objdump_parser.compile_units:
            tokens = dwarf_unit['producer'].split(' ')
            missing = [mo for mo in mandatory_optflags if mo not in tokens]
            forbidden = [f for f in forbidden_optflags if f in tokens]
            if missing:
                self.output.add_info('W', pkg, 'missing-mandatory-optflags', path, ' '.join(missing))
            if forbidden:
                self.output.add_info('E', pkg, 'forbidden-optflags', path, ' '.join(forbidden))

    def _is_standard_archive(self, pkg, pkgfile_path, path):
        # skip Klee bytecode archives
        if pkgfile_path.endswith('.bca'):
            return False

        # return false for e.g. Rust or Go packages that are archives
        # but files in the archive are not an ELF container
        ar_parser = ArParser(pkgfile_path)
        failed_reason = ar_parser.parsing_failed_reason
        if failed_reason:
            self.output.add_info('E', pkg, 'ar-failed', path, failed_reason)
            return False

        needles = ('__.PKGDEF', '_go_.o', 'lib.rmeta')
        return not any(needle for needle in needles if needle in ar_parser.objects)

    def _detect_attributes(self, magic):
        self.is_exec = 'executable' in magic
        self.is_shobj = 'shared object' in magic
        self.is_archive = 'current ar archive' in magic
        self.is_dynamically_linked = 'dynamically linked' in magic
        self.is_pie_exec = 'pie executable' in magic

    def run_elf_checks(self, pkg, pkgfile_path, path):
        if self.is_archive and not self._is_standard_archive(pkg, pkgfile_path, path):
            return

        self.readelf_parser = ReadelfParser(pkgfile_path, path)
        failed_reason = self.readelf_parser.parsing_failed_reason()
        if failed_reason:
            self.output.add_info('E', pkg, 'readelf-failed', path, failed_reason)
            return

        if not self.is_archive:
            if self.is_dynamically_linked:
                is_installed_pkg = isinstance(pkg, InstalledPkg) or isinstance(pkg, FakePkg)
                self.ldd_parser = LddParser(pkgfile_path, path, is_installed_pkg)
                failed_reason = self.ldd_parser.parsing_failed_reason
                if failed_reason:
                    self.output.add_info('E', pkg, 'ldd-failed', path, failed_reason)
                    return

            self.objdump_parser = ObjdumpParser(pkgfile_path, path)
            failed_reason = self.objdump_parser.parsing_failed_reason
            if failed_reason:
                self.output.add_info('E', pkg, 'objdump-failed', path, failed_reason)
                return

        with concurrent.futures.ThreadPoolExecutor() as executor:
            futures = []
            for fn in self.check_functions:
                futures.append(executor.submit(fn, pkg, pkgfile_path, path))
            concurrent.futures.wait(futures)
            for future in futures:
                err = future.exception()
                if err:
                    raise err

    def check_binary(self, pkg):
        exec_files = []
        multi_pkg = False
        pkg_has_lib = False
        pkg_has_binary = False
        pkg_has_binary_in_usrlib = False
        pkg_has_usrlib_file = False
        pkg_has_file_in_lib64 = False

        #  go through the all files, run files checks and collect data that are
        #  needed later
        for fname, pkgfile in pkg.files.items():

            # Common tests first
            self._check_libtool_wrapper(pkg, fname, pkgfile)
            self._check_invalid_la_file(pkg, fname)

            # consider non-binary in /usr/lib/ that is allowed by
            # UsrLibBinaryException config option as a "fake" binary and
            # do not throw 'only-non-binary-in-usr-lib' warning then
            if not stat.S_ISDIR(pkgfile.mode) and self.usr_lib_regex.search(fname):
                pkg_has_usrlib_file = True
                if not pkg_has_binary_in_usrlib and \
                        self.usr_lib_exception_regex.search(fname):
                    # Fake that we have binaries there to avoid
                    # only-non-binary-in-usr-lib false positives
                    pkg_has_binary_in_usrlib = True

            # find out if we have a file in /usr/lib64/ directory (needed later
            # for the package checks)
            if stat.S_ISREG(pkgfile.mode) and \
                    (fname.startswith('/usr/lib64') or
                     fname.startswith('/lib64')):
                pkg_has_file_in_lib64 = True

            # skip the rest of the tests for non-binaries
            # binary files only from here on
            is_ocaml_native = 'Objective caml native' in pkgfile.magic
            is_lua_bytecode = 'Lua bytecode' in pkgfile.magic
            if not (pkgfile.magic.startswith('ELF ') or 'current ar archive'
                    in pkgfile.magic or is_ocaml_native or is_lua_bytecode):
                continue

            self.checked_files += 1

            # mark this package as a one that has binary file
            pkg_has_binary = True

            # if there is a binary in /usr/lib then mark this package
            # accordingly
            if pkg_has_usrlib_file and not pkg_has_binary_in_usrlib and \
                    self.usr_lib_regex.search(fname):
                pkg_has_binary_in_usrlib = True

            self._check_binary_in_noarch(pkg, fname)

            # skip the rest of the tests for noarch packages
            # arch dependent packages only from here on
            if pkg.arch == 'noarch':
                continue

            self._check_binary_in_usr_share(pkg, fname)
            self._check_binary_in_etc(pkg, fname)

            # skip the rest of the tests for ocaml native, Lua bytecode,
            # Go .go and .gox, .o and .static
            if is_ocaml_native or is_lua_bytecode or fname.endswith('.o') or \
                    fname.endswith('.static') or fname.endswith('.gox') or \
                    fname.endswith('.go'):
                continue

            self._check_unstripped_binary(fname, pkg, pkgfile)

            # Detect attributes of an ELF file
            self._detect_attributes(pkgfile.magic)

            # run ELF checks
            self.run_elf_checks(pkg, pkgfile.path, fname)

            # inspect binary file
            is_shlib = self.readelf_parser.is_shlib

            if is_shlib:
                pkg_has_lib = True

            # skip non-exec and non-SO
            # executables and shared objects only from here on
            if not self.is_exec and not self.is_shobj:
                continue

            if self.is_shobj and not self.is_exec and '.so' not in fname and \
                    self.bin_regex.search(fname):
                # pkgfile.magic does not contain 'executable' for PIEs
                self.is_exec = True

            if self.is_exec:
                # add to the list of the all exec files
                if self.bin_regex.search(fname):
                    exec_files.append(fname)

                self._check_non_pie(pkg, fname)

        # find out if we have a multi-package
        srpm = pkg[rpm.RPMTAG_SOURCERPM]
        if srpm:
            srcname = self.srcname_regex.search(srpm)
            if srcname:
                multi_pkg = (pkg.name != srcname.group(1))

        # run checks for the whole package
        # it uses data collected in the previous for-cycle
        self._check_exec_in_library(pkg, pkg_has_lib, exec_files)
        self._check_non_versioned(pkg, pkg_has_lib, exec_files)
        self._check_no_binary(pkg, pkg_has_binary, multi_pkg,
                              pkg_has_file_in_lib64)
        self._check_noarch_with_lib64(pkg, pkg_has_file_in_lib64)
        self._check_only_non_binary_in_usrlib(pkg, pkg_has_usrlib_file,
                                              pkg_has_binary_in_usrlib)
