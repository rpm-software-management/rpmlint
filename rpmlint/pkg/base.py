import mmap
import os
from pathlib import Path
import re
import stat
import time
from urllib.parse import urljoin

import rpm
from rpmlint.helpers import byte_to_string
from rpmlint.pkg.utils import DepInfo, get_magic, has_magic, PREREQ_FLAG, stringToVersion


def _resolve_readlink(files, pkgfile):
    """
    Resolve symlinks for the given PkgFile, return the dereferenced
    PkgFile if it is found in this package, None if not.
    """
    result = pkgfile
    while result and result.linkto:
        linkpath = urljoin(result.name, result.linkto)
        linkpath = os.path.normpath(linkpath)
        result = files.get(linkpath)
    return result


# classes representing package

class AbstractPkg:
    _magic_from_compressed_re = re.compile(r'\([^)]+\s+compressed\s+data\b')

    def cleanup(self):
        pass

    def _calc_magic(self, pkgfile):
        magic_description = pkgfile.magic
        if not magic_description:
            if stat.S_ISDIR(pkgfile.mode):
                magic_description = 'directory'
            elif stat.S_ISLNK(pkgfile.mode):
                magic_description = "symbolic link to `%s'" % pkgfile.linkto
            elif not pkgfile.size:
                magic_description = 'empty'
        if not magic_description and not pkgfile.is_ghost and has_magic:
            start = time.monotonic()
            magic_description = get_magic(pkgfile.path)
            self.timers['libmagic'] += time.monotonic() - start
        if magic_description is None or self._magic_from_compressed_re.search(magic_description):
            # Discard magic from inside compressed files ('file -z')
            # until PkgFile gets decompression support.  We may get
            # such magic strings from package headers already now;
            # for example Fedora's rpmbuild as of F-11's 4.7.1 is
            # patched so it generates them.
            magic_description = ''
        return magic_description

    # internal function to gather dependency info used by the above ones
    def _gather_aux(self, header, xs, nametag, flagstag, versiontag,
                    prereq=None):
        versions = header[versiontag]

        if versions:
            names = header[nametag]
            flags = header[flagstag]
            for version, name_bytes, flag in zip(versions, names, flags):
                name = byte_to_string(name_bytes)
                evr = stringToVersion(byte_to_string(version))
                if prereq is not None and flag & PREREQ_FLAG:
                    prereq.append((name, flag & (~PREREQ_FLAG), evr))
                else:
                    xs.append(DepInfo(name, flag, evr))
        return xs, prereq

    def _gather_dep_info(self):
        _requires = []
        _prereq = []
        _provides = []
        _conflicts = []
        _obsoletes = []
        _recommends = []
        _suggests = []
        _enhances = []
        _supplements = []

        _requires, _prereq = self._gather_aux(self.header, _requires,
                                              rpm.RPMTAG_REQUIRENAME,
                                              rpm.RPMTAG_REQUIREFLAGS,
                                              rpm.RPMTAG_REQUIREVERSION,
                                              _prereq)
        _conflits, _ = self._gather_aux(self.header, _conflicts,
                                        rpm.RPMTAG_CONFLICTNAME,
                                        rpm.RPMTAG_CONFLICTFLAGS,
                                        rpm.RPMTAG_CONFLICTVERSION)
        _provides, _ = self._gather_aux(self.header, _provides,
                                        rpm.RPMTAG_PROVIDENAME,
                                        rpm.RPMTAG_PROVIDEFLAGS,
                                        rpm.RPMTAG_PROVIDEVERSION)
        _obsoletes, _ = self._gather_aux(self.header, _obsoletes,
                                         rpm.RPMTAG_OBSOLETENAME,
                                         rpm.RPMTAG_OBSOLETEFLAGS,
                                         rpm.RPMTAG_OBSOLETEVERSION)
        _recommends, _ = self._gather_aux(self.header, _recommends,
                                          rpm.RPMTAG_RECOMMENDNAME,
                                          rpm.RPMTAG_RECOMMENDFLAGS,
                                          rpm.RPMTAG_RECOMMENDVERSION)
        _suggests, _ = self._gather_aux(self.header, _suggests,
                                        rpm.RPMTAG_SUGGESTNAME,
                                        rpm.RPMTAG_SUGGESTFLAGS,
                                        rpm.RPMTAG_SUGGESTVERSION)
        _enhances, _ = self._gather_aux(self.header, _enhances,
                                        rpm.RPMTAG_ENHANCENAME,
                                        rpm.RPMTAG_ENHANCEFLAGS,
                                        rpm.RPMTAG_ENHANCEVERSION)
        _supplements, _ = self._gather_aux(self.header, _supplements,
                                           rpm.RPMTAG_SUPPLEMENTNAME,
                                           rpm.RPMTAG_SUPPLEMENTFLAGS,
                                           rpm.RPMTAG_SUPPLEMENTVERSION)

        return (_requires, _prereq, _provides, _conflicts, _obsoletes, _recommends,
                _suggests, _enhances, _supplements)

    def scriptprog(self, which):
        """
        Get the specified script interpreter as a string.
        Depending on rpm-python version, the string may or may not include
        interpreter arguments, if any.
        """
        if which is None:
            return ''
        prog = self[which]
        if prog is None:
            prog = ''
        elif isinstance(prog, (list, tuple)):
            # http://rpm.org/ticket/847#comment:2
            prog = ''.join(prog)
        return prog

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cleanup()

    def check_versioned_dep(self, name, version):
        # try to match name%_isa as well (e.g. 'foo(x86-64)', 'foo(x86-32)')
        name_re = re.compile(r'^%s(\(\w+-\d+\))?$' % re.escape(name))
        for d in self.requires + self.prereq:
            if name_re.match(d[0]):
                if d[1] & rpm.RPMSENSE_EQUAL != rpm.RPMSENSE_EQUAL \
                        or d[2][1] != version:
                    return False
                return True
        return False

    def read_with_mmap(self, filename):
        """Mmap a file, return it's content decoded."""
        try:
            with open(Path(self.dir_name() or '/', filename.lstrip('/'))) as in_file:
                return mmap.mmap(in_file.fileno(), 0, mmap.MAP_SHARED, mmap.PROT_READ).read().decode()
        except Exception:
            return ''

    def grep(self, regex, filename):
        """Grep regex from a file, return first matching line number (starting with 1)."""
        data = self.read_with_mmap(filename)
        match = regex.search(data)
        if match:
            return data.count('\n', 0, match.start()) + 1
        return None

    def readlink(self, pkgfile):
        """
        Resolve symlinks for the given PkgFile, return the dereferenced
        PkgFile if it is found in this package, None if not.
        """
        return _resolve_readlink(self.files, pkgfile)
