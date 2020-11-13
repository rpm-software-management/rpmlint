import re
import subprocess

from rpmlint.helpers import ENGLISH_ENVIROMENT


class LddParser:
    """
    Class contains all information obtained by ldd command
    about undefined symbols and unused direct dependencies.

    Parse these 2 outputs:

    $ ldd -u libnss-unused-dependency.so
    Unused direct dependencies:
        /lib/libnss_files.so.2

    $ ldd -r libthread-undefined-symbol.so
        linux-gate.so.1 (0xf7fce000)
        libc.so.6 => /lib/libc.so.6 (0xf7d9a000)
        /lib/ld-linux.so.2 (0xf7fcf000)
    undefined symbol: ps_pdwrite	(./libthread-undefined-symbol.so)
    undefined symbol: ps_pglobal_lookup	(./libthread-undefined-symbol.so)
    undefined symbol: ps_lsetregs	(./libthread-undefined-symbol.so)
    undefined symbol: ps_getpid	(./libthread-undefined-symbol.so)
    undefined symbol: ps_lgetfpregs	(./libthread-undefined-symbol.so)
    undefined symbol: ps_lsetfpregs	(./libthread-undefined-symbol.so)
    undefined symbol: ps_lgetregs	(./libthread-undefined-symbol.so)
    undefined symbol: ps_pdread	(./libthread-undefined-symbol.so)
    undefined symbol: gss_release_cred, version gssapi_krb5_2_MIT	(./test/ldd/libtirpc.so.3.0.0)
    undefined symbol: gss_canonicalize_name, version gssapi_krb5_2_MIT	(./test/ldd/libtirpc.so.3.0.0)
    undefined symbol: gss_pname_to_uid, version gssapi_krb5_2_MIT	(./test/ldd/libtirpc.so.3.0.0)
    undefined symbol: gss_accept_sec_context, version gssapi_krb5_2_MIT	(./test/ldd/libtirpc.so.3.0.0)
    undefined symbol: gss_verify_mic, version gssapi_krb5_2_MIT	(./test/ldd/libtirpc.so.3.0.0)
    undefined symbol: gss_get_mic, version gssapi_krb5_2_MIT	(./test/ldd/libtirpc.so.3.0.0)
    """

    unused_regex = re.compile(r'^\s+(?P<lib>\S+)')
    undef_regex = re.compile(r'^undefined symbol:\s+(?P<symbol>[^, ]+)')

    def __init__(self, pkgfile_path, path, is_installed_pkg):
        self.pkgfile_path = pkgfile_path
        self.dependencies = []
        self.unused_dependencies = []
        self.undefined_symbols = []
        self.parsing_failed_reason = None
        if is_installed_pkg:
            self.parse_dependencies()
            self.parse_undefined_symbols()

    def parse_dependencies(self):
        r = subprocess.run(['ldd', '-u', self.pkgfile_path], encoding='utf8',
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=ENGLISH_ENVIROMENT)
        if r.returncode == 0:
            return

        lines = r.stdout.splitlines()
        is_unused = False
        for line in lines:
            if line.startswith('Unused direct dependencies:'):
                is_unused = True
            elif is_unused:
                unused = self.unused_regex.search(line)
                if unused:
                    self.unused_dependencies.append(unused.group('lib'))
                else:
                    is_unused = False

    def parse_undefined_symbols(self):
        r = subprocess.run(['ldd', '-r', self.pkgfile_path], encoding='utf8',
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=ENGLISH_ENVIROMENT)
        # here ldd should always return 0
        if r.returncode != 0:
            self.parsing_failed_reason = r.stderr
            return

        lines = r.stdout.splitlines()
        for line in lines:
            r = self.undef_regex.search(line)
            if r:
                self.undefined_symbols.append(r.group('symbol'))
            else:
                self.dependencies.append(line.strip())

        # run c++filt demangler for all collected symbols
        if self.undefined_symbols:
            r = subprocess.run(['c++filt'] + self.undefined_symbols, encoding='utf8',
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=ENGLISH_ENVIROMENT)
            if r.returncode != 0:
                self.parsing_failed_reason = r.stderr
            else:
                self.undefined_symbols = r.stdout.splitlines()
