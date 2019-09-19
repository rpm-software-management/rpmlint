import concurrent.futures
from pathlib import Path
import re
import stat

import rpm
from rpmlint.checks.AbstractCheck import AbstractCheck
from rpmlint.lddparser import LddParser
from rpmlint.readelfparser import ReadelfParser
from rpmlint.stringsparser import StringsParser


class BinariesCheck(AbstractCheck):

    validso_regex = re.compile(r'(\.so\.\d+(\.\d+)*|\d\.so)$')
    soversion_regex = re.compile(r'.*?([0-9][.0-9]*)\.so|.*\.so\.([0-9][.0-9]*).*')
    usr_lib_regex = re.compile(r'^/usr/lib(64)?/')
    ldso_soname_regex = re.compile(r'^ld(-linux(-(ia|x86_)64))?\.so')

    numeric_dir_regex = re.compile(r'/usr(?:/share)/man/man./(.*)\.[0-9](?:\.gz|\.bz2)')
    versioned_dir_regex = re.compile(r'[^.][0-9]')
    so_regex = re.compile(r'/lib(64)?/[^/]+\.so(\.[0-9]+)*$')
    bin_regex = re.compile(r'^(/usr(/X11R6)?)?/s?bin/')
    reference_regex = re.compile(r'\.la$|^/usr/lib(64)?/pkgconfig/')
    srcname_regex = re.compile(r'(.*?)-[0-9]')
    invalid_dir_ref_regex = re.compile(r'/(home|tmp)(\W|$)')
    usr_arch_share_regex = re.compile(r'/share/.*/(?:x86|i.86|x86_64|ppc|ppc64|s390|s390x|ia64|m68k|arm|aarch64|mips|riscv)')

    def __init__(self, config, output):
        super().__init__(config, output)
        self.is_exec = False
        self.is_shobj = False
        self.system_lib_paths = config.configuration['SystemLibPaths']
        pie_exec_re = config.configuration['PieExecutables']
        self.pie_exec_re = re.compile(pie_exec_re) if pie_exec_re else None
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
                                self._check_executable_shlib]

    @staticmethod
    def create_nonlibc_regexp_call(call):
        r = r'(%s)\s?.*$' % call
        return re.compile(r)

    @staticmethod
    def create_regexp_call(call):
        r = r'(%s(?:@GLIBC\S+)?)(?:\s|$)' % call
        return re.compile(r)

    # For an archive, test if any .text sections is empty
    def _check_no_text_in_archive(self, pkg, pkgfile_path, path):
        if self.readelf_parser.is_archive:
            for comment in self.readelf_parser.comment_section_info.comments:
                if comment.startswith('GHC '):
                    return

            for elf_file in self.readelf_parser.section_info.elf_files:
                code_in_text = False
                for section in elf_file:
                    sn = section.name
                    if ((sn == '.preinit_array' or sn == '.init_array' or
                         sn == '.fini_array' or sn.startswith('.text')) and
                            section.size > 0):
                        code_in_text = True
                        break
                if not code_in_text:
                    self.output.add_info('E', pkg, 'lto-no-text-in-archive', path)
                    return

    def _check_missing_symtab_in_archive(self, pkg, pkgfile_path, path):
        if self.readelf_parser.is_archive:
            for elf_file in self.readelf_parser.section_info.elf_files:
                for section in elf_file:
                    if section.name == '.symtab':
                        return

            self.output.add_info('E', pkg, 'static-library-without-symtab', path)

    def _check_missing_debug_info_in_archive(self, pkg, pkgfile_path, path):
        if self.readelf_parser.is_archive:
            for elf_file in self.readelf_parser.section_info.elf_files:
                has_debug_info = any(['.debug_' in section.name for section in elf_file])
                if not has_debug_info:
                    self.output.add_info('E', pkg, 'static-library-without-debuginfo', path)
                    return

    # Check for LTO sections
    def _check_lto_section(self, pkg, pkgfile_path, path):
        for elf_file in self.readelf_parser.section_info.elf_files:
            for section in elf_file:
                if '.gnu.lto_.' in section.name:
                    self.output.add_info('E', pkg, 'lto-bytecode', path)
                    return

    def _check_executable_stack(self, pkg, pkgfile_path, path):
        if not self.readelf_parser.is_archive:
            stack_headers = [h for h in self.readelf_parser.program_header_info.headers if h.name == 'GNU_STACK']
            if not stack_headers:
                self.output.add_info('E', pkg, 'missing-PT_GNU_STACK-section', path)
            elif 'E' in stack_headers[0].flags:
                self.output.add_info('E', pkg, 'executable-stack', path)

    def _check_soname_symlink(self, pkg, file_path, soname):
        path = Path(file_path)
        symlink = path.parent / soname
        try:
            # check that we have a symlink with the soname in the package
            # and it points to the checked shared library
            link = pkg.files()[str(symlink)].linkto
            if link not in (file_path, path.parent, ''):
                self.output.add_info('E', pkg, 'invalid-ldconfig-symlink', file_path, link)
        except KeyError:
            # if we do not have a symlink, report an issue
            if path.name.startswith('lib') or path.name.startswith('ld-'):
                self.output.add_info('E', pkg, 'no-ldconfig-symlink', file_path)

    def _check_shared_library(self, pkg, pkgfile_path, path):
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

                res = self.soversion_regex.search(soname)
                if res:
                    soversion = res.group(1) or res.group(2)
                    if soversion and soversion not in pkg.name:
                        self.output.add_info('E', pkg, 'incoherent-version-in-name', soversion)

        if not self.readelf_parser.section_info.pic:
            self.output.add_info('E', pkg, 'shlib-with-non-pic-code', path)

    def _check_dependency(self, pkg, pkgfile_path, path):
        # following issues are errors for shared libs and warnings for executables
        if not self.readelf_parser.is_archive and not self.readelf_parser.is_debug:
            info_type = 'E' if self.readelf_parser.is_shlib else 'W'
            for symbol in self.ldd_parser.undefined_symbols:
                self.output.add_info(info_type, pkg, 'undefined-non-weak-symbol', path, symbol)
            for dependency in self.ldd_parser.unused_dependencies:
                self.output.add_info(info_type, pkg, 'unused-direct-shlib-dependency',
                                     path, dependency)

    def _check_library_dependency_location(self, pkg, pkgfile_path, path):
        if not self.readelf_parser.is_archive:
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
        dyn_section = self.readelf_parser.dynamic_section_info
        if not len(dyn_section.needed) and not (dyn_section.soname and
                                                self.ldso_soname_regex.search(dyn_section.soname)):
            if self.is_shobj:
                msg = 'shared-lib-without-dependency-information'
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
                self.output.add_info('E', pkg, msg, path)

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
        if strings_parser.parsing_failed:
            self.output.add_info('E', pkg, 'strings-failed', path)
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
                self.output.add_info('E', pkg, 'shared-lib-not-executable', path)

    def run_elf_checks(self, pkg, pkgfile_path, path):
        self.readelf_parser = ReadelfParser(pkgfile_path, path)
        if self.readelf_parser.parsing_failed():
            self.output.add_info('E', pkg, 'readelf-failed', path)
            return

        if not self.readelf_parser.is_archive:
            self.ldd_parser = LddParser(pkgfile_path, path)
            if self.ldd_parser.parsing_failed:
                self.output.add_info('E', pkg, 'ldd-failed', path)
                return

        with concurrent.futures.ThreadPoolExecutor() as executor:
            futures = []
            for fn in self.check_functions:
                futures.append(executor.submit(fn, pkg, pkgfile_path, path))
            concurrent.futures.wait(futures)

    def check_binary(self, pkg):
        files = pkg.files()
        exec_files = []
        has_lib = False
        binary = False
        binary_in_usr_lib = False
        has_usr_lib_file = False
        file_in_lib64 = False

        multi_pkg = False
        srpm = pkg[rpm.RPMTAG_SOURCERPM]
        if srpm:
            res = self.srcname_regex.search(srpm)
            if res:
                multi_pkg = (pkg.name != res.group(1))

        for fname, pkgfile in files.items():

            if not stat.S_ISDIR(pkgfile.mode) and self.usr_lib_regex.search(fname):
                has_usr_lib_file = True
                if not binary_in_usr_lib and \
                        self.usr_lib_exception_regex.search(fname):
                    # Fake that we have binaries there to avoid
                    # only-non-binary-in-usr-lib false positives
                    binary_in_usr_lib = True

            if stat.S_ISREG(pkgfile.mode) and \
                    (fname.startswith('/usr/lib64') or fname.startswith('/lib64')):
                file_in_lib64 = True

            is_ocaml_native = 'Objective caml native' in pkgfile.magic
            is_lua_bytecode = 'Lua bytecode' in pkgfile.magic

            if 'shell script' in pkgfile.magic:
                file_start = None
                try:
                    with open(pkgfile.path, 'rb') as inputf:
                        file_start = inputf.read(2048)
                except IOError:
                    pass
                if (file_start and b'This wrapper script should never '
                        b'be moved out of the build directory' in file_start):
                    self.output.add_info('E', pkg, 'libtool-wrapper-in-package', fname)

            if not (pkgfile.magic.startswith('ELF ') or 'current ar archive' in pkgfile.magic or is_ocaml_native or is_lua_bytecode):
                if self.reference_regex.search(fname):
                    lines = pkg.grep(self.invalid_dir_ref_regex, fname)
                    if lines:
                        self.output.add_info('E', pkg, 'invalid-directory-reference', fname,
                                             '(line %s)' % ', '.join(lines))
                continue

            # binary files only from here on
            binary = True

            if has_usr_lib_file and not binary_in_usr_lib and \
                    self.usr_lib_regex.search(fname):
                binary_in_usr_lib = True

            if pkg.arch == 'noarch':
                self.output.add_info('E', pkg,
                                     'arch-independent-package-contains-binary-or-object',
                                     fname)
                continue

            # arch dependent packages only from here on

            # in /usr/share ?
            if fname.startswith('/usr/share/') and not self.usr_arch_share_regex.search(fname):
                self.output.add_info('E', pkg, 'arch-dependent-file-in-usr-share', fname)

            # in /etc ?
            if fname.startswith('/etc/'):
                self.output.add_info('E', pkg, 'binary-in-etc', fname)

            if is_ocaml_native or is_lua_bytecode or fname.endswith('.o') or \
                    fname.endswith('.static'):
                continue

            # stripped ?
            if 'not stripped' in pkgfile.magic:
                self.output.add_info('W', pkg, 'unstripped-binary-or-object', fname)

            self.is_exec = 'executable' in pkgfile.magic
            self.is_shobj = 'shared object' in pkgfile.magic
            is_pie_exec = 'pie executable' in pkgfile.magic

            # run ELF checks
            self.run_elf_checks(pkg, pkgfile.path, fname)

            # inspect binary file
            is_shlib = self.readelf_parser.is_shlib

            if is_shlib:
                has_lib = True

            if not self.is_exec and not self.is_shobj:
                continue

            if self.is_shobj and not self.is_exec and '.so' not in fname and \
                    self.bin_regex.search(fname):
                # pkgfile.magic does not contain 'executable' for PIEs
                self.is_exec = True

            if self.is_exec:
                if self.bin_regex.search(fname):
                    exec_files.append(fname)

                if not self.is_shobj and not is_pie_exec:
                    if self.pie_exec_re and self.pie_exec_re.search(fname):
                        self.output.add_info('E', pkg, 'non-position-independent-executable',
                                             fname)
                    else:
                        self.output.add_info('W', pkg, 'position-independent-executable-suggested',
                                             fname)

        if has_lib:
            for f in exec_files:
                self.output.add_info('E', pkg, 'executable-in-library-package', f)
            for f in files:
                res = self.numeric_dir_regex.search(f)
                fn = res and res.group(1) or f
                if f not in exec_files and not self.so_regex.search(f) and \
                        not self.versioned_dir_regex.search(fn):
                    self.output.add_info('E', pkg, 'non-versioned-file-in-library-package', f)

        if not binary and not multi_pkg and not file_in_lib64 and pkg.arch != 'noarch':
            self.output.add_info('E', pkg, 'no-binary')

        if pkg.arch == 'noarch' and file_in_lib64:
            self.output.add_info('E', pkg, 'noarch-with-lib64')

        if has_usr_lib_file and not binary_in_usr_lib:
            self.output.add_info('W', pkg, 'only-non-binary-in-usr-lib')
