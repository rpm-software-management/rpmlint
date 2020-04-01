import bz2
from collections import namedtuple
import gzip
import lzma
import os
from pathlib import Path
import re
from shlex import quote
import stat
import subprocess
import tempfile
from urllib.parse import urljoin

try:
    import magic
    # TODO: magic.MAGIC_COMPRESS when PkgFile gets decompress support.
    _magic = magic.open(magic.MAGIC_NONE)
    _ = _magic.descriptor  # magic >= 5.05 needed
    _magic.load()
except ImportError:
    _magic = None
import rpm
from rpmlint.helpers import byte_to_string, ENGLISH_ENVIROMENT, print_warning
from rpmlint.pkgfile import PkgFile


DepInfo = namedtuple('DepInfo', ('name', 'flags', 'version'))

# 64: RPMSENSE_PREREQ is 0 with rpm 4.4..4.7, we want 64 here in order
# to do the right thing with those versions and packages built with other
# rpm versions
PREREQ_FLAG = (rpm.RPMSENSE_PREREQ or 64) | rpm.RPMSENSE_SCRIPT_PRE | \
    rpm.RPMSENSE_SCRIPT_POST | rpm.RPMSENSE_SCRIPT_PREUN | \
    rpm.RPMSENSE_SCRIPT_POSTUN

SCRIPT_TAGS = [
    (rpm.RPMTAG_PREIN, rpm.RPMTAG_PREINPROG, '%pre'),
    (rpm.RPMTAG_POSTIN, rpm.RPMTAG_POSTINPROG, '%post'),
    (rpm.RPMTAG_PREUN, rpm.RPMTAG_PREUNPROG, '%preun'),
    (rpm.RPMTAG_POSTUN, rpm.RPMTAG_POSTUNPROG, '%postun'),
    (rpm.RPMTAG_TRIGGERSCRIPTS, rpm.RPMTAG_TRIGGERSCRIPTPROG, '%trigger'),
    (rpm.RPMTAG_PRETRANS, rpm.RPMTAG_PRETRANSPROG, '%pretrans'),
    (rpm.RPMTAG_POSTTRANS, rpm.RPMTAG_POSTTRANSPROG, '%posttrans'),
    (rpm.RPMTAG_VERIFYSCRIPT, rpm.RPMTAG_VERIFYSCRIPTPROG, '%verifyscript'),
    # file triggers: rpm >= 4.12.90
    (getattr(rpm, 'RPMTAG_FILETRIGGERSCRIPTS', 5066),
     getattr(rpm, 'RPMTAG_FILETRIGGERSCRIPTPROG', 5067),
     '%filetrigger'),
    (getattr(rpm, 'RPMTAG_TRANSFILETRIGGERSCRIPTS', 5076),
     getattr(rpm, 'RPMTAG_TRANSFILETRIGGERSCRIPTPROG', 5077),
     '%transfiletrigger'),
]

RPM_SCRIPTLETS = ('pre', 'post', 'preun', 'postun', 'pretrans', 'posttrans',
                  'trigger', 'triggerin', 'triggerprein', 'triggerun',
                  'triggerpostun', 'verifyscript', 'filetriggerin',
                  'filetrigger', 'filetriggerun', 'filetriggerpostun',
                  'transfiletriggerin', 'transfiletrigger',
                  'transfiletriggerun', 'transfiletriggerun',
                  'transfiletriggerpostun')


gzip_regex = re.compile(r'\.t?gz?$')
bz2_regex = re.compile(r'\.t?bz2?$')
xz_regex = re.compile(r'\.(t[xl]z|xz|lzma)$')


def catcmd(fname):
    """Get a 'cat' command that handles possibly compressed files."""
    fname = str(fname)
    cat = 'gzip -dcf'
    if bz2_regex.search(fname):
        cat = 'bzip2 -dcf'
    elif xz_regex.search(fname):
        cat = 'xz -dc'
    return cat


def compression_algorithm(fname):
    """Return compression algorithm based on filename if known, None otherwise."""
    fname = str(fname)
    if gzip_regex.search(fname):
        return gzip
    elif bz2_regex.search(fname):
        return bz2
    elif xz_regex.search(fname):
        return lzma
    else:
        return None


def is_utf8(fname):
    compression = compression_algorithm(fname)
    if compression is None:
        with open(fname, 'rb') as f:
            return is_utf8_bytestr(f.read())

    with compression.open(fname, 'rb') as f:
        try:
            return is_utf8_bytestr(f.read())
        except OSError:
            return True


def is_utf8_bytestr(s):
    """Returns True whether the given text is UTF-8.
    Due to changes in rpm, needs to handle both bytes and unicode."""
    try:
        if hasattr(s, 'decode'):
            s.decode('utf-8')
        elif hasattr(s, 'encode'):
            s.encode('utf-8')
        else:
            unexpected = type(s).__name__
            raise TypeError(
                'Expected str/unicode/bytes, not {}'.format(unexpected))
    except UnicodeError:
        return False
    return True


def has_forbidden_controlchars(val):
    if isinstance(val, str) or isinstance(val, bytes):
        string = val
        if isinstance(val, bytes):
            val = memoryview(val)
        for c in val:
            if isinstance(c, str):
                c = ord(c)
            if c < 32 and (c not in (9, 10, 13)):
                return string
    if isinstance(val, tuple) or isinstance(val, list):
        for item in val:
            return has_forbidden_controlchars(item)
    return False


# from yum 3.2.27, rpmUtils.miscutils, with rpmlint modifications
def compareEVR(evr1, evr2):
    (e1, v1, r1) = evr1
    (e2, v2, r2) = evr2
    # return 1: a is newer than b
    # 0: a and b are the same version
    # -1: b is newer than a
    # rpmlint mod: don't stringify None epochs to 'None' strings
    if e1 is not None:
        e1 = str(e1)
    v1 = str(v1)
    r1 = str(r1)
    if e2 is not None:
        e2 = str(e2)
    v2 = str(v2)
    r2 = str(r2)
    rc = rpm.labelCompare((e1, v1, r1), (e2, v2, r2))
    return rc


# from yum 3.2.27, rpmUtils.miscutils, with rpmlint modifications
def rangeCompare(reqtuple, provtuple):
    """returns true if provtuple satisfies reqtuple"""
    (reqn, reqf, (reqe, reqv, reqr)) = reqtuple
    (n, f, (e, v, r)) = provtuple
    if reqn != n:
        return 0

    # unversioned satisfies everything
    if not f or not reqf:
        return 1

    # and you thought we were done having fun
    # if the requested release is left out then we have
    # to remove release from the package prco to make sure the match
    # is a success - ie: if the request is EQ foo 1:3.0.0 and we have
    # foo 1:3.0.0-15 then we have to drop the 15 so we can match
    if reqr is None:
        r = None
    # rpmlint mod: don't mess with provided Epoch, doing so breaks e.g.
    # 'Requires: foo < 1.0' should not be satisfied by 'Provides: foo = 1:0.5'
    # if reqe is None:
    #    e = None
    if reqv is None:  # just for the record if ver is None then we're going to segfault
        v = None

    # if we just require foo-version, then foo-version-* will match
    if r is None:
        reqr = None

    rc = compareEVR((e, v, r), (reqe, reqv, reqr))

    # does not match unless
    if rc >= 1:
        if reqf in ['GT', 'GE', 4, 12]:
            return 1
        if reqf in ['EQ', 8]:
            if f in ['LE', 10, 'LT', 2]:
                return 1
        if reqf in ['LE', 'LT', 'EQ', 10, 2, 8]:
            if f in ['LE', 'LT', 10, 2]:
                return 1

    if rc == 0:
        if reqf in ['GT', 4]:
            if f in ['GT', 'GE', 4, 12]:
                return 1
        if reqf in ['GE', 12]:
            if f in ['GT', 'GE', 'EQ', 'LE', 4, 12, 8, 10]:
                return 1
        if reqf in ['EQ', 8]:
            if f in ['EQ', 'GE', 'LE', 8, 12, 10]:
                return 1
        if reqf in ['LE', 10]:
            if f in ['EQ', 'LE', 'LT', 'GE', 8, 10, 2, 12]:
                return 1
        if reqf in ['LT', 2]:
            if f in ['LE', 'LT', 10, 2]:
                return 1
    if rc <= -1:
        if reqf in ['GT', 'GE', 'EQ', 4, 12, 8]:
            if f in ['GT', 'GE', 4, 12]:
                return 1
        if reqf in ['LE', 'LT', 10, 2]:
            return 1
#                if rc >= 1:
#                    if reqf in ['GT', 'GE', 4, 12]:
#                        return 1
#                if rc == 0:
#                    if reqf in ['GE', 'LE', 'EQ', 8, 10, 12]:
#                        return 1
#                if rc <= -1:
#                    if reqf in ['LT', 'LE', 2, 10]:
#                        return 1

    return 0


# from yum 3.2.23, rpmUtils.miscutils, with rpmlint modifications
def formatRequire(name, flags, evr):
    s = name

    if flags:
        if flags & (rpm.RPMSENSE_LESS | rpm.RPMSENSE_GREATER |
                    rpm.RPMSENSE_EQUAL):
            s = s + ' '
            if flags & rpm.RPMSENSE_LESS:
                s = s + '<'
            if flags & rpm.RPMSENSE_GREATER:
                s = s + '>'
            if flags & rpm.RPMSENSE_EQUAL:
                s = s + '='
            s = '%s %s' % (s, versionToString(evr))
    return s


def versionToString(evr):
    if not isinstance(evr, (list, tuple)):
        # assume string
        return evr
    ret = ''
    if evr[0] is not None and evr[0] != '':
        ret += str(evr[0]) + ':'
    if evr[1] is not None:
        ret += evr[1]
        if evr[2] is not None and evr[2] != '':
            ret += '-' + evr[2]
    return ret


# from yum 3.2.23, rpmUtils.miscutils, with some rpmlint modifications
def stringToVersion(verstring):
    if verstring in (None, ''):
        return (None, None, None)
    epoch = None
    i = verstring.find(':')
    if i != -1:
        try:
            epoch = str(int(verstring[:i]))
        except ValueError:
            # garbage in epoch, ignore it
            pass
    i += 1
    j = verstring.find('-', i)
    if j != -1:
        if verstring[i:j] == '':
            version = None
        else:
            version = verstring[i:j]
        release = verstring[j + 1:]
    else:
        if verstring[i:] == '':
            version = None
        else:
            version = verstring[i:]
        release = None
    return (epoch, version, release)


def parse_deps(line):
    """
    Parse provides/requires/conflicts/obsoletes line to list of
    (name, flags, (epoch, version, release)) tuples.
    """

    prcos = []
    tokens = re.split(r'[\s,]+', line.strip())

    # Drop line continuation backslash in multiline macro definition (for
    # spec file parsing), e.g.
    # [...] \
    # Obsoletes: foo-%1 <= 1.0.0 \
    # [...] \
    # (yes, this is an ugly hack and we probably have other problems with
    #  multiline macro definitions elsewhere...)
    if tokens[-1] == '\\':
        del tokens[-1]

    prco = []
    while tokens:
        token = tokens.pop(0)
        if not token:
            # skip empty tokens
            continue

        plen = len(prco)

        if plen == 0:
            prco.append(token)

        elif plen == 1:
            flags = 0
            if token[0] in ('=', '<', '<=', '>', '>='):
                # versioned, flags
                if '=' in token:
                    flags |= rpm.RPMSENSE_EQUAL
                if '<' in token:
                    flags |= rpm.RPMSENSE_LESS
                if '>' in token:
                    flags |= rpm.RPMSENSE_GREATER
                prco.append(flags)
            else:
                # no flags following name, treat as unversioned, add and reset
                prco.extend((flags, (None, None, None)))
                prcos.append(tuple(prco))
                prco = [token]

        elif plen == 2:
            # last token of versioned one, add and reset
            prco.append(stringToVersion(token))
            prcos.append(tuple(prco))
            prco = []

    plen = len(prco)
    if plen:
        if plen == 1:
            prco.extend((0, (None, None, None)))
        elif plen == 2:
            prco.append((None, None, None))
        prcos.append(tuple(prco))

    return prcos


# classes representing package

class AbstractPkg(object):

    def cleanup(self):
        pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cleanup()


class Pkg(AbstractPkg):

    _magic_from_compressed_re = re.compile(r'\([^)]+\s+compressed\s+data\b')

    def __init__(self, filename, dirname, header=None, is_source=False, extracted=False):
        self.filename = filename
        self.extracted = extracted
        self.dirname = self.dir_name(dirname)
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
         self.supplements) = self._gatherDepInfo()

        self.req_names = [x[0] for x in self.requires + self.prereq]

        self.files = self._gatherFilesInfo()
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
        else:
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
            return val

    # return the name of the directory where the package is extracted
    def dirName(self):
        return self.dirname

    def dir_name(self, dirname):
        return self._extract(dirname)

    # extract rpm contents
    def _extract(self, dirname):
        if not Path(dirname).is_dir():
            print_warning('Unable to access dir %s' % dirname)
        else:
            dirname = dirname if dirname != '/' else None
            self.__tmpdir = tempfile.TemporaryDirectory(
                prefix='rpmlint.%s.' % Path(self.filename).name, dir=dirname
            )
            dirname = self.__tmpdir.name
            # TODO: sequence based command invocation
            # TODO: warn some way if this fails (e.g. rpm2cpio not installed)
            command_str = \
                'rpm2cpio %(f)s | cpio -id -D %(d)s ; chmod -R +rX %(d)s' % \
                {'f': quote(str(self.filename)), 'd': quote(dirname)}
            subprocess.run(command_str, shell=True, env=ENGLISH_ENVIROMENT)
            self.extracted = True
        return dirname

    def checkSignature(self):
        ret = subprocess.run(('rpm', '-K', self.filename), stdout=subprocess.PIPE, stderr=subprocess.STDOUT, env=ENGLISH_ENVIROMENT)
        text = ret.stdout.decode()
        if text.endswith('\n'):
            text = text[:-1]
        return ret.returncode, text

    # remove the extracted files from the package
    def cleanup(self):
        if self.extracted and self.dirname:
            self.__tmpdir.cleanup()

    def grep(self, regex, filename):
        """Grep regex from a file, return matching line numbers."""
        ret = []
        lineno = 0
        try:
            with open(Path(self.dirName() or '/', filename.lstrip('/'))) as in_file:
                for line in in_file:
                    lineno += 1
                    if regex.search(line):
                        ret.append(str(lineno))
                        break
        except Exception:
            pass
        return ret

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
    def _gatherFilesInfo(self):

        ret = {}
        flags = self.header[rpm.RPMTAG_FILEFLAGS]
        modes = self.header[rpm.RPMTAG_FILEMODES]
        users = self.header[rpm.RPMTAG_FILEUSERNAME]
        groups = self.header[rpm.RPMTAG_FILEGROUPNAME]
        links = [byte_to_string(x) for x in self.header[rpm.RPMTAG_FILELINKTOS]]
        sizes = self.header[rpm.RPMTAG_FILESIZES]
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
            for idx in range(0, len(files)):
                pkgfile = PkgFile(files[idx])
                pkgfile.path = os.path.normpath(os.path.join(
                    self.dirName() or '/', pkgfile.name.lstrip('/')))
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
                if not pkgfile.magic:
                    if stat.S_ISDIR(pkgfile.mode):
                        pkgfile.magic = 'directory'
                    elif stat.S_ISLNK(pkgfile.mode):
                        pkgfile.magic = "symbolic link to `%s'" % pkgfile.linkto
                    elif not pkgfile.size:
                        pkgfile.magic = 'empty'
                if (not pkgfile.magic and
                        not pkgfile.is_ghost and _magic):
                    # file() method evaluates every file twice with python2,
                    # use descriptor() method instead
                    try:
                        fd = os.open(pkgfile.path, os.O_RDONLY)
                        pkgfile.magic = byte_to_string(_magic.descriptor(fd))
                        os.close(fd)
                    except OSError:
                        pass
                if pkgfile.magic is None:
                    pkgfile.magic = ''
                elif Pkg._magic_from_compressed_re.search(pkgfile.magic):
                    # Discard magic from inside compressed files ('file -z')
                    # until PkgFile gets decompression support.  We may get
                    # such magic strings from package headers already now;
                    # for example Fedora's rpmbuild as of F-11's 4.7.1 is
                    # patched so it generates them.
                    pkgfile.magic = ''
                if filecaps:
                    pkgfile.filecaps = filecaps[idx]
                ret[pkgfile.name] = pkgfile
        return ret

    def readlink(self, pkgfile):
        """
        Resolve symlinks for the given PkgFile, return the dereferenced
        PkgFile if it is found in this package, None if not.
        """
        result = pkgfile
        while result and result.linkto:
            linkpath = urljoin(result.name, result.linkto)
            linkpath = os.path.normpath(linkpath)
            result = self.files.get(linkpath)
        return result

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

    # internal function to gather dependency info used by the above ones
    def _gather_aux(self, header, xs, nametag, flagstag, versiontag,
                    prereq=None):
        names = header[nametag]
        flags = header[flagstag]
        versions = header[versiontag]

        if versions:
            for loop in range(len(versions)):
                name = byte_to_string(names[loop])
                evr = stringToVersion(byte_to_string(versions[loop]))
                if prereq is not None and flags[loop] & PREREQ_FLAG:
                    prereq.append((name, flags[loop] & (~PREREQ_FLAG), evr))
                else:
                    xs.append(DepInfo(name, flags[loop], evr))
        return xs, prereq

    def _gatherDepInfo(self):
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


def getInstalledPkgs(name):
    """Get list of installed package objects by name."""

    pkgs = []
    ts = rpm.TransactionSet()
    if re.search(r'[?*]|\[.+\]', name):
        mi = ts.dbMatch()
        mi.pattern('name', rpm.RPMMIRE_GLOB, name)
    else:
        mi = ts.dbMatch('name', name)

    for hdr in mi:
        pkgs.append(InstalledPkg(name, hdr))

    return pkgs


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

    def checkSignature(self):
        return (0, 'fake: pgp md5 OK')


# Class to provide an API to a 'fake' package, eg. for specfile-only checks
class FakePkg(AbstractPkg):
    def __init__(self, name, files=None):
        self.name = str(name)
        self.arch = None
        self.current_linenum = None
        self.dirname = None

        # files are dictionary where key is name of a file
        self.files = {f.name: f for f in files} if files else {}

    def dirName(self):
        if not self.dirname:
            self.__tmpdir = tempfile.TemporaryDirectory(prefix='rpmlint.%s.' % Path(self.name).name)
            self.dirname = self.__tmpdir.name
        return self.dirname

    def cleanup(self):
        if self.dirname:
            self.__tmpdir.cleanup()
