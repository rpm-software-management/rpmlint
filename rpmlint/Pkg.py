# -*- coding: utf-8 -*-
#############################################################################
# File          : Pkg.py
# Package       : rpmlint
# Author        : Frederic Lepied
# Created on    : Tue Sep 28 07:18:06 1999
# Purpose       : provide an API to handle a rpm package either by accessing
#                 the rpm file or by accessing the files contained inside.
#############################################################################

from __future__ import print_function

import os
import re
import stat
import subprocess
import sys
import tempfile
try:
    from urlparse import urljoin
except ImportError:
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

import rpmlint.Filter

# utilities

# b2s():  bytes to str
if sys.version_info[0] > 2:
    long = int
    unicode = str

    def b2s(b):
        if b is None or isinstance(b, str):
            return b
        if isinstance(b, (list, tuple)):
            return [b2s(x) for x in b]
        return b.decode(errors='replace')
else:
    def b2s(b):
        return b

try:
    from shlex import quote as shquote
except ImportError:
    def shquote(s):
        return '"%s"' % s


def warn(s):
    """
    Print warning message to stderr.
    """
    print(s, file=sys.stderr)


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
    (getattr(rpm, "RPMTAG_FILETRIGGERSCRIPTS", 5066),
     getattr(rpm, "RPMTAG_FILETRIGGERSCRIPTPROG", 5067),
     '%filetrigger'),
    (getattr(rpm, "RPMTAG_TRANSFILETRIGGERSCRIPTS", 5076),
     getattr(rpm, "RPMTAG_TRANSFILETRIGGERSCRIPTPROG", 5077),
     '%transfiletrigger'),
]

RPM_SCRIPTLETS = ('pre', 'post', 'preun', 'postun', 'pretrans', 'posttrans',
                  'trigger', 'triggerin', 'triggerprein', 'triggerun',
                  'triggerpostun', 'verifyscript', 'filetriggerin',
                  'filetrigger', 'filetriggerun', 'filetriggerpostun',
                  'transfiletriggerin', 'transfiletrigger',
                  'transfiletriggerun', 'transfiletriggerun',
                  'transfiletriggerpostun')

var_regex = re.compile(r'^(.*)\${?(\w+)}?(.*)$')


def shell_var_value(var, script):
    assign_regex = re.compile(r'\b' + re.escape(var) +
                              r'\s*=\s*(.+)\s*(#.*)*$', re.MULTILINE)
    res = assign_regex.search(script)
    if res:
        res2 = var_regex.search(res.group(1))
        if res2:
            if res2.group(2) == var:  # infinite loop
                return None
        return substitute_shell_vars(res.group(1), script)
    else:
        return None


def substitute_shell_vars(val, script):
    res = var_regex.search(val)
    if res:
        value = shell_var_value(res.group(2), script)
        if not value:
            value = ''
        return res.group(1) + value + \
            substitute_shell_vars(res.group(3), script)
    else:
        return val


def getstatusoutput(cmd, stdoutonly=False, shell=False, raw=False, lc_all="C"):
    """
    A version of commands.getstatusoutput() which can take cmd as a
    sequence, thus making it potentially more secure.
    """
    env = dict(os.environ, LC_ALL=lc_all)
    if stdoutonly:
        proc = subprocess.Popen(cmd, shell=shell, stdin=subprocess.PIPE,
                                stdout=subprocess.PIPE, close_fds=True, env=env)
    else:
        proc = subprocess.Popen(cmd, shell=shell, stdin=subprocess.PIPE,
                                stdout=subprocess.PIPE, env=env,
                                stderr=subprocess.STDOUT, close_fds=True)
    proc.stdin.close()
    with proc.stdout:
        text = proc.stdout.read()
    sts = proc.wait()
    if not raw:
        text = b2s(text)
        if text.endswith('\n'):
            text = text[:-1]
    if sts is None:
        sts = 0
    return sts, text


bz2_regex = re.compile(r'\.t?bz2?$')
xz_regex = re.compile(r'\.(t[xl]z|xz|lzma)$')


def catcmd(fname):
    """Get a 'cat' command that handles possibly compressed files."""
    cat = 'gzip -dcf'
    if bz2_regex.search(fname):
        cat = 'bzip2 -dcf'
    elif xz_regex.search(fname):
        cat = 'xz -dc'
    return cat


def is_utf8(fname):
    (sts, output) = getstatusoutput(catcmd(fname).split() + [fname], raw=True)
    return not sts and is_utf8_bytestr(output)


def is_utf8_bytestr(s):
    try:
        s.decode('UTF-8')
    except UnicodeError:
        return False
    return True


def to_unicode(string):
    if string is None:
        return unicode('')
    elif isinstance(string, unicode):
        return string
    for enc in ('utf-8', 'iso-8859-1', 'iso-8859-15', 'iso-8859-2'):
        try:
            x = unicode(string, enc)
        except UnicodeError:
            pass
        else:
            if x.encode(enc) == string:
                return x
    return unicode(string, "ascii", errors="replace")


def readlines(path):
    with open(path, 'rb') as fobj:
        for line in fobj:
            yield b2s(line)


def mktemp():
    tmpfd, tmpname = tempfile.mkstemp(prefix='rpmlint.')
    tmpfile = os.fdopen(tmpfd, 'w')
    return tmpfile, tmpname


slash_regex = re.compile(r'/+')
slashdot_regex = re.compile(r'/(\.(/|$))+')
slashend_regex = re.compile(r'([^/])/+$')


def safe_normpath(path):
    """
    Like os.path.normpath but normalizes less aggressively thus being
    potentially safer for paths containing symlinks.
    """
    ret = slash_regex.sub('/', path)
    ret = slashdot_regex.sub('\\2', ret)
    ret = slashend_regex.sub('\\1', ret)
    return ret


def get_default_valid_rpmgroups(filename=None):
    """
    Get default rpm groups from filename, or try to look them up from
    the rpm package (if installed) if no filename is given.
    """
    groups = []
    if not filename:
        try:
            with InstalledPkg("rpm") as p:
                groupsfiles = [x for x in p.files() if x.endswith('/GROUPS')]
                if groupsfiles:
                    filename = groupsfiles[0]
        except KeyError:  # the rpm package might not be installed
            pass
    if filename and os.path.exists(filename):
        with open(filename) as fobj:
            groups = fobj.read().strip().splitlines()
        if 'Development/Debug' not in groups:
            groups.append('Development/Debug')
        if 'Unspecified' not in groups:  # auto-added by rpm >= 4.6.0
            groups.append('Unspecified')
        groups.sort()
    return groups


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
    # "Requires: foo < 1.0" should not be satisfied by "Provides: foo = 1:0.5"
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
            s = s + " "
            if flags & rpm.RPMSENSE_LESS:
                s = s + "<"
            if flags & rpm.RPMSENSE_GREATER:
                s = s + ">"
            if flags & rpm.RPMSENSE_EQUAL:
                s = s + "="
            s = "%s %s" % (s, versionToString(evr))
    return s


def versionToString(evr):
    if not isinstance(evr, (list, tuple)):
        # assume string
        return evr
    ret = ""
    if evr[0] is not None and evr[0] != "":
        ret += str(evr[0]) + ":"
    if evr[1] is not None:
        ret += evr[1]
        if evr[2] is not None and evr[2] != "":
            ret += "-" + evr[2]
    return ret


# from yum 3.2.23, rpmUtils.miscutils, with some rpmlint modifications
def stringToVersion(verstring):
    if verstring in (None, ''):
        return (None, None, None)
    epoch = None
    i = verstring.find(':')
    if i != -1:
        try:
            epoch = str(long(verstring[:i]))
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
            if token[0] in ("=", "<", "<=", ">", ">="):
                # versioned, flags
                if "=" in token:
                    flags |= rpm.RPMSENSE_EQUAL
                if "<" in token:
                    flags |= rpm.RPMSENSE_LESS
                if ">" in token:
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

    def __init__(self, filename, dirname, header=None, is_source=False):
        self.filename = filename
        self.extracted = False
        self.dirname = dirname
        self.current_linenum = None
        self._config_files = None
        self._doc_files = None
        self._noreplace_files = None
        self._ghost_files = None
        self._missingok_files = None
        self._files = None
        self._requires = None
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
        if self.isNoSource():
            self.arch = 'nosrc'
        elif self.isSource():
            self.arch = 'src'
        else:
            self.arch = self.header.format("%{ARCH}")

    # Return true if the package is a source package
    def isSource(self):
        return self.is_source

    # Return true if the package is a nosource package.
    # NoSource files are ghosts in source packages.
    def isNoSource(self):
        return self.is_source and self.ghostFiles()

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
                val = b2s(val)
            return val

    # return the name of the directory where the package is extracted
    def dirName(self):
        if not self.extracted:
            self._extract()
        return self.dirname

    # extract rpm contents
    def _extract(self):
        if not os.path.isdir(self.dirname):
            warn('Unable to access dir %s' % self.dirname)
            return None
        else:
            self.dirname = tempfile.mkdtemp(
                prefix='rpmlint.%s.' % os.path.basename(self.filename),
                dir=self.dirname)
            # TODO: sequence based command invocation
            # TODO: warn some way if this fails (e.g. rpm2cpio not installed)
            command_str = \
                'rpm2cpio %(f)s | (cd %(d)s; cpio -id); chmod -R +rX %(d)s' % \
                {'f': shquote(self.filename), 'd': shquote(self.dirname)}
            cmd = getstatusoutput(command_str, shell=True)
            self.extracted = True
            return cmd

    def checkSignature(self):
        return getstatusoutput(('rpm', '-K', self.filename))

    # remove the extracted files from the package
    def cleanup(self):
        if self.extracted and self.dirname:
            getstatusoutput(('rm', '-rf', self.dirname))

    def grep(self, regex, filename):
        """Grep regex from a file, return matching line numbers."""
        ret = []
        lineno = 0
        try:
            with open(os.path.join(
                    self.dirName() or '/', filename.lstrip('/'))) as in_file:
                for line in in_file:
                    lineno += 1
                    if regex.search(line):
                        ret.append(str(lineno))
                        break
        except Exception as e:
            Filter.printWarning(self, 'read-error', filename, e)
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

    # return the associative array indexed on file names with
    # the values as: (file perm, file owner, file group, file link to)
    def files(self):
        if self._files is not None:
            return self._files

        self._gatherFilesInfo()
        return self._files

    # return the list of config files
    def configFiles(self):
        if self._config_files is not None:
            return self._config_files

        self._config_files = [x.name for x in self.files().values()
                              if x.is_config]
        return self._config_files

    # return the list of noreplace files
    def noreplaceFiles(self):
        if self._noreplace_files is not None:
            return self._noreplace_files

        self._noreplace_files = [x.name for x in self.files().values()
                                 if x.is_noreplace]
        return self._noreplace_files

    # return the list of documentation files
    def docFiles(self):
        if self._doc_files is not None:
            return self._doc_files

        self._doc_files = [x.name for x in self.files().values() if x.is_doc]
        return self._doc_files

    # return the list of ghost files
    def ghostFiles(self):
        if self._ghost_files is not None:
            return self._ghost_files

        self._ghost_files = [x.name for x in self.files().values()
                             if x.is_ghost]
        return self._ghost_files

    def missingOkFiles(self):
        if self._missingok_files is not None:
            return self._missingok_files

        self._missingok_files = [x.name for x in self.files().values()
                                 if x.is_missingok]
        return self._missingok_files

    # extract information about the files
    def _gatherFilesInfo(self):

        self._files = {}
        flags = self.header[rpm.RPMTAG_FILEFLAGS]
        modes = self.header[rpm.RPMTAG_FILEMODES]
        users = self.header[rpm.RPMTAG_FILEUSERNAME]
        groups = self.header[rpm.RPMTAG_FILEGROUPNAME]
        links = [b2s(x) for x in self.header[rpm.RPMTAG_FILELINKTOS]]
        sizes = self.header[rpm.RPMTAG_FILESIZES]
        md5s = self.header[rpm.RPMTAG_FILEMD5S]
        mtimes = self.header[rpm.RPMTAG_FILEMTIMES]
        rdevs = self.header[rpm.RPMTAG_FILERDEVS]
        langs = self.header[rpm.RPMTAG_FILELANGS]
        inodes = self.header[rpm.RPMTAG_FILEINODES]
        requires = [b2s(x) for x in self.header[rpm.RPMTAG_FILEREQUIRE]]
        provides = [b2s(x) for x in self.header[rpm.RPMTAG_FILEPROVIDE]]
        files = [b2s(x) for x in self.header[rpm.RPMTAG_FILENAMES]]
        magics = [b2s(x) for x in self.header[rpm.RPMTAG_FILECLASS]]
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
                pkgfile.user = b2s(users[idx])
                pkgfile.group = b2s(groups[idx])
                pkgfile.linkto = links[idx] and safe_normpath(links[idx])
                pkgfile.size = sizes[idx]
                pkgfile.md5 = md5s[idx]
                pkgfile.mtime = mtimes[idx]
                pkgfile.rdev = rdevs[idx]
                pkgfile.inode = inodes[idx]
                pkgfile.requires = parse_deps(requires[idx])
                pkgfile.provides = parse_deps(provides[idx])
                pkgfile.lang = b2s(langs[idx])
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
                        pkgfile.magic = b2s(_magic.descriptor(fd))
                        os.close(fd)
                    except OSError:
                        pass
                if pkgfile.magic is None:
                    pkgfile.magic = ''
                elif Pkg._magic_from_compressed_re.search(pkgfile.magic):
                    # Discard magic from inside compressed files ("file -z")
                    # until PkgFile gets decompression support.  We may get
                    # such magic strings from package headers already now;
                    # for example Fedora's rpmbuild as of F-11's 4.7.1 is
                    # patched so it generates them.
                    pkgfile.magic = ''
                if filecaps:
                    pkgfile.filecaps = filecaps[idx]
                self._files[pkgfile.name] = pkgfile

    def readlink(self, pkgfile):
        """
        Resolve symlinks for the given PkgFile, return the dereferenced
        PkgFile if it is found in this package, None if not.
        """
        result = pkgfile
        while result and result.linkto:
            linkpath = urljoin(result.name, result.linkto)
            linkpath = safe_normpath(linkpath)
            result = self.files().get(linkpath)
        return result

    # API to access dependency information
    def obsoletes(self):
        """
        Get package Obsoletes as list of
        (name, flags, (epoch, version, release)) tuples.
        """
        self._gatherDepInfo()
        return self._obsoletes

    def requires(self):
        """
        Get package Requires as list of
        (name, flags, (epoch, version, release)) tuples.
        """
        self._gatherDepInfo()
        return self._requires

    def prereq(self):
        """
        Get package PreReqs as list of
        (name, flags, (epoch, version, release)) tuples.
        """
        self._gatherDepInfo()
        return self._prereq

    def req_names(self):
        if self._req_names == -1:
            self._req_names = [x[0] for x in self.requires() + self.prereq()]
        return self._req_names

    def check_versioned_dep(self, name, version):
        # try to match name%_isa as well (e.g. "foo(x86-64)", "foo(x86-32)")
        name_re = re.compile(r'^%s(\(\w+-\d+\))?$' % re.escape(name))
        for d in self.requires() + self.prereq():
            if name_re.match(d[0]):
                if d[1] & rpm.RPMSENSE_EQUAL != rpm.RPMSENSE_EQUAL \
                        or d[2][1] != version:
                    return False
                return True
        return False

    def conflicts(self):
        """
        Get package Conflicts as list of
        (name, flags, (epoch, version, release)) tuples.
        """
        self._gatherDepInfo()
        return self._conflicts

    def provides(self):
        """
        Get package Provides as list of
        (name, flags, (epoch, version, release)) tuples.
        """
        self._gatherDepInfo()
        return self._provides

    def recommends(self):
        """
        Get package Recommends as list of
        (name, flags, (epoch, version, release)) tuples.
        """
        self._gatherDepInfo()
        return self._recommends

    def suggests(self):
        """
        Get package Suggests as list of
        (name, flags, (epoch, version, release)) tuples.
        """
        self._gatherDepInfo()
        return self._suggests

    def enhances(self):
        """
        Get package Enhances as list of
        (name, flags, (epoch, version, release)) tuples.
        """
        self._gatherDepInfo()
        return self._enhances

    def supplements(self):
        """
        Get package Supplements as list of
        (name, flags, (epoch, version, release)) tuples.
        """
        self._gatherDepInfo()
        return self._supplements

    # internal function to gather dependency info used by the above ones
    def _gather_aux(self, header, list, nametag, flagstag, versiontag,
                    prereq=None):
        names = header[nametag]
        flags = header[flagstag]
        versions = header[versiontag]

        if versions:
            for loop in range(len(versions)):
                name = b2s(names[loop])
                evr = stringToVersion(b2s(versions[loop]))
                if prereq is not None and flags[loop] & PREREQ_FLAG:
                    prereq.append((name, flags[loop] & (~PREREQ_FLAG), evr))
                else:
                    list.append((name, flags[loop], evr))

    def _gatherDepInfo(self):
        if self._requires is None:
            self._requires = []
            self._prereq = []
            self._provides = []
            self._conflicts = []
            self._obsoletes = []
            self._recommends = []
            self._suggests = []
            self._enhances = []
            self._supplements = []

            self._gather_aux(self.header, self._requires,
                             rpm.RPMTAG_REQUIRENAME,
                             rpm.RPMTAG_REQUIREFLAGS,
                             rpm.RPMTAG_REQUIREVERSION,
                             self._prereq)
            self._gather_aux(self.header, self._conflicts,
                             rpm.RPMTAG_CONFLICTNAME,
                             rpm.RPMTAG_CONFLICTFLAGS,
                             rpm.RPMTAG_CONFLICTVERSION)
            self._gather_aux(self.header, self._provides,
                             rpm.RPMTAG_PROVIDENAME,
                             rpm.RPMTAG_PROVIDEFLAGS,
                             rpm.RPMTAG_PROVIDEVERSION)
            self._gather_aux(self.header, self._obsoletes,
                             rpm.RPMTAG_OBSOLETENAME,
                             rpm.RPMTAG_OBSOLETEFLAGS,
                             rpm.RPMTAG_OBSOLETEVERSION)
            if hasattr(rpm, "RPMTAG_RECOMMENDNAME"):  # rpm >= 4.12
                self._gather_aux(self.header, self._recommends,
                                 rpm.RPMTAG_RECOMMENDNAME,
                                 rpm.RPMTAG_RECOMMENDFLAGS,
                                 rpm.RPMTAG_RECOMMENDVERSION)
            if hasattr(rpm, "RPMTAG_SUGGESTNAME"):  # rpm >= 4.12
                self._gather_aux(self.header, self._suggests,
                                 rpm.RPMTAG_SUGGESTNAME,
                                 rpm.RPMTAG_SUGGESTFLAGS,
                                 rpm.RPMTAG_SUGGESTVERSION)
            if hasattr(rpm, "RPMTAG_ENHANCENAME"):  # rpm >= 4.12
                self._gather_aux(self.header, self._enhances,
                                 rpm.RPMTAG_ENHANCENAME,
                                 rpm.RPMTAG_ENHANCEFLAGS,
                                 rpm.RPMTAG_ENHANCEVERSION)
            if hasattr(rpm, "RPMTAG_SUPPLEMENTNAME"):  # rpm >= 4.12
                self._gather_aux(self.header, self._supplements,
                                 rpm.RPMTAG_SUPPLEMENTNAME,
                                 rpm.RPMTAG_SUPPLEMENTFLAGS,
                                 rpm.RPMTAG_SUPPLEMENTVERSION)

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
            prog = "".join(prog)
        return prog


def getInstalledPkgs(name):
    """Get list of installed package objects by name."""

    pkgs = []
    ts = rpm.TransactionSet()
    if re.search(r'[?*]|\[.+\]', name):
        mi = ts.dbMatch()
        mi.pattern("name", rpm.RPMMIRE_GLOB, name)
    else:
        mi = ts.dbMatch("name", name)

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

        Pkg.__init__(self, name, '/', hdr)

        self.extracted = True
        # create a fake filename to satisfy some checks on the filename
        self.filename = '%s-%s-%s.%s.rpm' % \
            (self.name, self[rpm.RPMTAG_VERSION], self[rpm.RPMTAG_RELEASE],
             self[rpm.RPMTAG_ARCH])

    def cleanup(self):
        pass

    def checkSignature(self):
        return (0, 'fake: pgp md5 OK')


# Class to provide an API to a "fake" package, eg. for specfile-only checks
class FakePkg(AbstractPkg):
    def __init__(self, name):
        self.name = name
        self.arch = None
        self.current_linenum = None
        self.dirname = None

    def dirName(self):
        if not self.dirname:
            self.dirname = tempfile.mkdtemp(
                prefix='rpmlint.%s.' % os.path.basename(self.name))
        return self.dirname

    def cleanup(self):
        if self.dirname:
            getstatusoutput(('rm', '-rf', self.dirname))


# Class for files in packages
class PkgFile(object):

    def __init__(self, name):
        self.name = name
        # Real path to the file (taking extract dir into account)
        self.path = name
        self.flags = 0
        self.mode = 0
        self.user = None
        self.group = None
        self.linkto = ''
        self.size = None
        self.md5 = None
        self.mtime = 0
        self.rdev = ''
        self.inode = 0
        self.requires = []
        self.provides = []
        self.lang = ''
        self.magic = ''
        self.filecaps = None

    # TODO: decompression support

    is_config = property(lambda self: self.flags & rpm.RPMFILE_CONFIG)
    is_doc = property(lambda self: self.flags & rpm.RPMFILE_DOC)
    is_noreplace = property(lambda self: self.flags & rpm.RPMFILE_NOREPLACE)
    is_ghost = property(lambda self: self.flags & rpm.RPMFILE_GHOST)
    is_missingok = property(lambda self: self.flags & rpm.RPMFILE_MISSINGOK)


if __name__ == '__main__':
    for p in sys.argv[1:]:
        with Pkg(p, tempfile.gettempdir()) as pkg:
            print('Requires: %s' % pkg.requires())
            print('Prereq: %s' % pkg.prereq())
            print('Conflicts: %s' % pkg.conflicts())
            print('Provides: %s' % pkg.provides())
            print('Obsoletes: %s' % pkg.obsoletes())

# Pkg.py ends here
