import os
from pathlib import Path
import re
from shlex import quote
import shutil
import subprocess
import tempfile
import time

import rpm
from rpmlint.helpers import (byte_to_string, ENGLISH_ENVIRONMENT,
                             print_warning, pushd)
from rpmlint.pkg.base import AbstractPkg
from rpmlint.pkg.utils import parse_deps, SCRIPT_TAGS
from rpmlint.pkgfile import PkgFile


class Pkg(AbstractPkg):
    def __init__(self, filename, dirname, header=None, is_source=False, extracted=False, verbose=False):
        self.filename = filename
        self.extracted = extracted

        # record decompression and extraction time
        start = time.monotonic()
        self.dirname = self._extract_rpm(dirname, verbose)
        self.timers = {'ExtractRpm': time.monotonic() - start, 'libmagic': 0}
        self.current_linenum = None

        self._req_names = -1

        if header:
            self.header = header
            self.is_source = is_source
        else:
            # Create a package object from the file name
            ts = rpm.TransactionSet()
            # Don't check signatures here...
            ts.setVSFlags(rpm._RPMVSF_NOSIGNATURES)
            fd = os.open(filename, os.O_RDONLY)
            try:
                self.header = ts.hdrFromFdno(fd)
            finally:
                os.close(fd)
            self.is_source = not self.header[rpm.RPMTAG_SOURCERPM]

        self.name = self[rpm.RPMTAG_NAME]

        (self.requires, self.prereq, self.provides, self.conflicts,
         self.obsoletes, self.recommends, self.suggests, self.enhances,
         self.supplements) = self._gather_dep_info()

        self.req_names = [x[0] for x in self.requires + self.prereq]

        self.files = self._gather_files_info()
        self.config_files = [x.name for x in self.files.values() if x.is_config]
        self.doc_files = [x.name for x in self.files.values() if x.is_doc]
        self.ghost_files = [x.name for x in self.files.values() if x.is_ghost]
        self.noreplace_files = [x.name for x in self.files.values() if x.is_noreplace]
        self.missingok_files = [x.name for x in self.files.values() if x.is_missingok]

        if self.is_no_source:
            self.arch = 'nosrc'
        elif self.is_source:
            self.arch = 'src'
        else:
            self.arch = self.header.format('%{ARCH}')

    # Return true if the package is a nosource package.
    # NoSource files are ghosts in source packages.
    @property
    def is_no_source(self):
        return self.is_source and self.ghost_files

    # access the tags like an array
    def __getitem__(self, key):
        try:
            val = self.header[key]
        except KeyError:
            val = []
        if val == []:
            return None
        # Note that text tags we want to try decoding for real in TagsCheck
        # such as summary, description and changelog are not here.
        if key in (rpm.RPMTAG_NAME, rpm.RPMTAG_VERSION, rpm.RPMTAG_RELEASE,
                   rpm.RPMTAG_ARCH, rpm.RPMTAG_GROUP, rpm.RPMTAG_BUILDHOST,
                   rpm.RPMTAG_LICENSE, rpm.RPMTAG_HEADERI18NTABLE,
                   rpm.RPMTAG_PACKAGER, rpm.RPMTAG_SOURCERPM,
                   rpm.RPMTAG_DISTRIBUTION, rpm.RPMTAG_VENDOR) \
        or key in (x[0] for x in SCRIPT_TAGS) \
        or key in (x[1] for x in SCRIPT_TAGS):
            val = byte_to_string(val)
            if key == rpm.RPMTAG_GROUP and val == 'Unspecified':
                val = None
        return val

    # return the name of the directory where the package is extracted
    def dir_name(self):
        return self.dirname

    def _extract_rpm(self, dirname, verbose):
        if not Path(dirname).is_dir():
            print_warning('Unable to access dir %s' % dirname)
        elif dirname == '/':
            # it is an InstalledPkg
            pass
        else:
            self.__tmpdir = tempfile.TemporaryDirectory(
                prefix='rpmlint.%s.' % Path(self.filename).name, dir=dirname
            )
            dirname = self.__tmpdir.name

            # BusyBox' cpio does not support '-D' argument and the only safe
            # usage is doing chdir before invocation.
            filename = Path(self.filename).resolve()
            with pushd(dirname):
                stderr = None if verbose else subprocess.DEVNULL
                # SUSE-specific: never print stderr
                stderr = subprocess.DEVNULL
                if shutil.which('rpm2archive'):
                    with open(filename, 'rb') as rpm_data:
                        subprocess.check_output('rpm2archive - | tar -xz && chmod -R +rX .', shell=True, env=ENGLISH_ENVIRONMENT,
                                                stderr=stderr, stdin=rpm_data)
                else:
                    command_str = f'rpm2cpio {quote(str(filename))} | cpio -id && chmod -R +rX .'
                    subprocess.check_output(command_str, shell=True, env=ENGLISH_ENVIRONMENT, stderr=stderr)
            self.extracted = True
        return dirname

    def check_signature(self):
        ret = subprocess.run(('rpm', '-Kv', self.filename),
                             stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                             env=ENGLISH_ENVIRONMENT, text=True)
        text = ret.stdout
        if text.endswith('\n'):
            text = text[:-1]
        return ret.returncode, text

    # remove the extracted files from the package
    def cleanup(self):
        if self.extracted and self.dirname:
            self.__tmpdir.cleanup()

    def langtag(self, tag, lang):
        """Get value of tag in the given language."""
        # LANGUAGE trumps other env vars per GNU gettext docs, see also #166
        orig = os.environ.get('LANGUAGE')
        os.environ['LANGUAGE'] = lang
        ret = self[tag]
        if orig is not None:
            os.environ['LANGUAGE'] = orig
        return ret

    # extract information about the files
    def _gather_files_info(self):
        ret = {}
        flags = self.header[rpm.RPMTAG_FILEFLAGS]
        modes = self.header[rpm.RPMTAG_FILEMODES]
        users = self.header[rpm.RPMTAG_FILEUSERNAME]
        groups = self.header[rpm.RPMTAG_FILEGROUPNAME]
        links = [byte_to_string(x) for x in self.header[rpm.RPMTAG_FILELINKTOS]]
        sizes = self.header[rpm.RPMTAG_FILESIZES]
        if len(sizes) != len(flags):
            sizes = self.header[rpm.RPMTAG_LONGFILESIZES]
        md5s = self.header[rpm.RPMTAG_FILEMD5S]
        mtimes = self.header[rpm.RPMTAG_FILEMTIMES]
        rdevs = self.header[rpm.RPMTAG_FILERDEVS]
        langs = self.header[rpm.RPMTAG_FILELANGS]
        inodes = self.header[rpm.RPMTAG_FILEINODES]
        requires = [byte_to_string(x) for x in self.header[rpm.RPMTAG_FILEREQUIRE]]
        provides = [byte_to_string(x) for x in self.header[rpm.RPMTAG_FILEPROVIDE]]
        files = [byte_to_string(x) for x in self.header[rpm.RPMTAG_FILENAMES]]
        magics = [byte_to_string(x) for x in self.header[rpm.RPMTAG_FILECLASS]]
        try:  # rpm >= 4.7.0
            filecaps = self.header[rpm.RPMTAG_FILECAPS]
        except AttributeError:
            filecaps = None

        # rpm-python < 4.6 does not return a list for this (or FILEDEVICES,
        # FWIW) for packages containing exactly one file
        if not isinstance(inodes, list):
            inodes = [inodes]

        if files:
            for idx, file in enumerate(files):
                pkgfile = PkgFile(file)
                pkgfile.path = os.path.normpath(os.path.join(
                    self.dir_name() or '/', pkgfile.name.lstrip('/')))
                pkgfile.flags = flags[idx]
                pkgfile.mode = modes[idx]
                pkgfile.user = byte_to_string(users[idx])
                pkgfile.group = byte_to_string(groups[idx])
                pkgfile.linkto = links[idx] and os.path.normpath(links[idx])
                pkgfile.size = sizes[idx]
                pkgfile.md5 = md5s[idx]
                pkgfile.mtime = mtimes[idx]
                pkgfile.rdev = rdevs[idx]
                pkgfile.inode = inodes[idx]
                pkgfile.requires = parse_deps(requires[idx])
                pkgfile.provides = parse_deps(provides[idx])
                pkgfile.lang = byte_to_string(langs[idx])
                pkgfile.magic = magics[idx]
                pkgfile.magic = self._calc_magic(pkgfile)
                if filecaps:
                    pkgfile.filecaps = byte_to_string(filecaps[idx])
                ret[pkgfile.name] = pkgfile
        return ret

    def get_core_reqs(self):
        """
        Return the list of dependencies that are not found by find-requires
        withouth the flag RPM
        """
        core_reqs = []

        for dep in rpm.ds(self.header, 'requires'):
            # skip deps which were found by find-requires
            if dep.Flags() & rpm.RPMSENSE_FIND_REQUIRES != 0:
                continue
            core_reqs.append(dep.N())

        return core_reqs


def get_installed_pkgs(name):
    """Get list of installed package objects by name."""

    ts = rpm.TransactionSet()
    if re.search(r'[?*]|\[.+\]', name):
        mi = ts.dbMatch()
        mi.pattern('name', rpm.RPMMIRE_GLOB, name)
    else:
        mi = ts.dbMatch('name', name)

    return [InstalledPkg(name, hdr) for hdr in mi]


# Class to provide an API to an installed package
class InstalledPkg(Pkg):
    def __init__(self, name, hdr=None):
        if not hdr:
            ts = rpm.TransactionSet()
            mi = ts.dbMatch('name', name)
            if not mi:
                raise KeyError(name)
            try:
                hdr = next(mi)
            except StopIteration:
                raise KeyError(name)

        super().__init__(name, '/', hdr, extracted=True)
        # create a fake filename to satisfy some checks on the filename
        self.filename = '%s-%s-%s.%s.rpm' % \
            (self.name, self[rpm.RPMTAG_VERSION], self[rpm.RPMTAG_RELEASE],
             self[rpm.RPMTAG_ARCH])

    def cleanup(self):
        pass

    def check_signature(self):
        return (0, 'fake: pgp md5 OK')
