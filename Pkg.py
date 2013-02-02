# -*- coding: utf-8 -*-
#############################################################################
# File          : Pkg.py
# Package       : rpmlint
# Author        : Frederic Lepied
# Created on    : Tue Sep 28 07:18:06 1999
# Purpose       : provide an API to handle a rpm package either by accessing
#                 the rpm file or by accessing the files contained inside.
#############################################################################

import commands
import os
import re
import subprocess
import sys
import tempfile
import types
import urlparse

try:
    import magic
    # TODO: magic.MAGIC_COMPRESS when PkgFile gets decompress support.
    _magic = magic.open(magic.MAGIC_NONE)
    _magic.load()
except:
    _magic = None
import rpm

import Filter

# Python 2/3 compatibility/convenience wrapper for printing to stderr with
# less concerns of UnicodeErrors than plain sys.stderr.write.
if sys.version_info[0] > 2:
    # Blows up with Python < 3 without the exec() hack
    exec('def warn(s): print (s, file=sys.stderr)')
else:
    def warn(s): print >> sys.stderr, s


# utilities

# 64: RPMSENSE_PREREQ is 0 with recent rpm versions, we want 64 here in order
# to do the right thing with packages built with older rpm versions
PREREQ_FLAG = (rpm.RPMSENSE_PREREQ or 64) | \
              rpm.RPMSENSE_SCRIPT_PRE | \
              rpm.RPMSENSE_SCRIPT_POST | \
              rpm.RPMSENSE_SCRIPT_PREUN | \
              rpm.RPMSENSE_SCRIPT_POSTUN

var_regex = re.compile('^(.*)\${?(\w+)}?(.*)$')

def shell_var_value(var, script):
    assign_regex = re.compile('\\b' + re.escape(var) + '\s*=\s*(.+)\s*(#.*)*$',
                              re.MULTILINE)
    res = assign_regex.search(script)
    if res:
        res2 = var_regex.search(res.group(1))
        if res2:
            if res2.group(2) == var: # infinite loop
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

def getstatusoutput(cmd, stdoutonly = False):
    '''A version of commands.getstatusoutput() which can take cmd as a
       sequence, thus making it potentially more secure.'''
    if stdoutonly:
        proc = subprocess.Popen(cmd, stdin=subprocess.PIPE,
                                stdout=subprocess.PIPE, close_fds=True)
    else:
        proc = subprocess.Popen(cmd, stdin=subprocess.PIPE,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT, close_fds=True)
    proc.stdin.close()
    text = proc.stdout.read()
    sts = proc.wait()
    if sts is None:
        sts = 0
    if text.endswith('\n'):
        text = text[:-1]
    return sts, text

bz2_regex = re.compile('\.t?bz2?$')
xz_regex = re.compile('\.(t[xl]z|xz|lzma)$')

def catcmd(fname):
    """Get a 'cat' command that handles possibly compressed files."""
    cat = 'gzip -dcf'
    if bz2_regex.search(fname):
        cat = 'bzip2 -dcf'
    elif xz_regex.search(fname):
        cat = 'xz -dc'
    return cat

def is_utf8(fname):
    (sts, text) = getstatusoutput(catcmd(fname).split() + [fname])
    return not sts and is_utf8_str(text)

def is_utf8_str(s):
    try:
        s.decode('UTF-8')
    except:
        return False
    return True

def to_utf8(string):
    if string is None:
        return ''
    elif isinstance(string, unicode):
        return string
    try:
        x = unicode(string, 'ascii')
        return string
    except UnicodeError:
        encodings = ['utf-8', 'iso-8859-1', 'iso-8859-15', 'iso-8859-2']
        for enc in encodings:
            try:
                x = unicode(string, enc)
            except UnicodeError:
                pass
            else:
                if x.encode(enc) == string:
                    return x.encode('utf-8')
    newstring = ''
    for char in string:
        if ord(char) > 127:
            newstring = newstring + '?'
        else:
            newstring = newstring + char
    return newstring

def readlines(path):
    fobj = open(path, "r")
    try:
        return fobj.readlines()
    finally:
        fobj.close()

def mktemp():
    tmpfd, tmpname = tempfile.mkstemp(prefix = 'rpmlint.')
    tmpfile = os.fdopen(tmpfd, 'w')
    return tmpfile, tmpname

slash_regex = re.compile('/+')
slashdot_regex = re.compile('/(\.(/|$))+')
slashend_regex = re.compile('([^/])/+$')

def safe_normpath(path):
    """Like os.path.normpath but normalizes less aggressively thus being
    potentially safer for paths containing symlinks."""
    ret = slash_regex.sub('/', path)
    ret = slashdot_regex.sub('\\2', ret)
    ret = slashend_regex.sub('\\1', ret)
    return ret

def get_default_valid_rpmgroups(filename = None):
    """Get default rpm groups from filename, or try to look them up from
    the rpm package (if installed) if no filename is given"""
    groups = []
    if not filename:
        try:
            p = InstalledPkg('rpm')
        except:
            pass
        else:
            groupsfiles = [x for x in p.files() if x.endswith('/GROUPS')]
            if groupsfiles:
                filename = groupsfiles[0]
    if filename and os.path.exists(filename):
        fobj = open(filename)
        try:
            groups = fobj.read().strip().splitlines()
        finally:
            fobj.close()
        if 'Development/Debug' not in groups:
            groups.append('Development/Debug')
        if 'Unspecified' not in groups: # auto-added by rpm >= 4.6.0
            groups.append('Unspecified')
        groups.sort()
    return groups

# from yum 3.2.27, rpmUtils.miscutils, with rpmlint modifications
def compareEVR((e1, v1, r1), (e2, v2, r2)):
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
    #if reqe is None:
    #    e = None
    if reqv is None: # just for the record if ver is None then we're going to segfault
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
    if not isinstance(evr, tuple) and not isinstance(evr, list):
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
        release = verstring[j+1:]
    else:
        if verstring[i:] == '':
            version = None
        else:
            version = verstring[i:]
        release = None
    return (epoch, version, release)

def parse_deps(line):
    '''Parse provides/requires/conflicts/obsoletes line to list of
       (name, flags, (epoch, version, release)) tuples.'''

    prcos = []
    tokens = re.split('[\s,]+', line.strip())

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

class Pkg:

    _magic_from_compressed_re = re.compile('\([^)]+\s+compressed\s+data\\b')

    def __init__(self, filename, dirname, header = None, is_source = False):
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

        self.name = self.header[rpm.RPMTAG_NAME]
        if self.isNoSource():
            self.arch = 'nosrc'
        elif self.isSource():
            self.arch = 'src'
        else:
            self.arch = self.header[rpm.RPMTAG_ARCH]

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
        except:
            val = []
        if val == []:
            return None
        else:
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
                prefix = 'rpmlint.%s.' % os.path.basename(self.filename),
                dir = self.dirname)
            # TODO: better shell escaping or sequence based command invocation
            command_str = \
                'rpm2cpio "%s" | (cd "%s"; cpio -id); chmod -R +rX "%s"' % \
                (self.filename, self.dirname, self.dirname)
            cmd = commands.getstatusoutput(command_str)
            self.extracted = True
            return cmd

    def checkSignature(self):
        return getstatusoutput(('env', 'LC_ALL=C', 'rpm', '-K', self.filename))

    # remove the extracted files from the package
    def cleanup(self):
        if self.extracted and self.dirname:
            getstatusoutput(('rm', '-rf', self.dirname))

    def grep(self, regex, filename):
        """Grep regex from a file, return matching line numbers."""
        ret = []
        lineno = 0
        in_file = None
        try:
            try:
                in_file = open(self.dirName() + '/' + filename)
                for line in in_file:
                    lineno += 1
                    if regex.search(line):
                        ret.append(str(lineno))
                        break
            except Exception, e:
                Filter.printWarning(self, 'read-error', filename, e)
        finally:
            if in_file:
                in_file.close()
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
        links = self.header[rpm.RPMTAG_FILELINKTOS]
        sizes = self.header[rpm.RPMTAG_FILESIZES]
        md5s = self.header[rpm.RPMTAG_FILEMD5S]
        mtimes = self.header[rpm.RPMTAG_FILEMTIMES]
        rdevs = self.header[rpm.RPMTAG_FILERDEVS]
        langs = self.header[rpm.RPMTAG_FILELANGS]
        inodes = self.header[rpm.RPMTAG_FILEINODES]
        requires = self.header[rpm.RPMTAG_FILEREQUIRE]
        provides = self.header[rpm.RPMTAG_FILEPROVIDE]
        files = self.header[rpm.RPMTAG_FILENAMES]
        magics = self.header[rpm.RPMTAG_FILECLASS]
        try: # rpm >= 4.7.0
            filecaps = self.header[rpm.RPMTAG_FILECAPS]
        except:
            filecaps = None

        # rpm-python < 4.6 does not return a list for this (or FILEDEVICES,
        # FWIW) for packages containing exactly one file
        if not isinstance(inodes, types.ListType):
            inodes = [inodes]

        if files:
            for idx in range(0, len(files)):
                pkgfile = PkgFile(files[idx])
                # Do not use os.path.join here, pkgfile.name can start with a
                # / which would result in self.dirName being ignored
                pkgfile.path = os.path.normpath(
                    self.dirName() + '/' + pkgfile.name)
                pkgfile.flags = flags[idx]
                pkgfile.mode = modes[idx]
                pkgfile.user = users[idx]
                pkgfile.group = groups[idx]
                pkgfile.linkto = links[idx] and safe_normpath(links[idx])
                pkgfile.size = sizes[idx]
                pkgfile.md5 = md5s[idx]
                pkgfile.mtime = mtimes[idx]
                pkgfile.rdev = rdevs[idx]
                pkgfile.inode = inodes[idx]
                pkgfile.requires = parse_deps(requires[idx])
                pkgfile.provides = parse_deps(provides[idx])
                pkgfile.lang = langs[idx]
                pkgfile.magic = magics[idx]
                if not pkgfile.magic and _magic:
                    pkgfile.magic = _magic.file(pkgfile.path)
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
        """Resolve symlinks for the given PkgFile, return the dereferenced
           PkgFile if it is found in this package, None if not."""
        result = pkgfile
        while result and result.linkto:
            linkpath = urlparse.urljoin(result.name, result.linkto)
            linkpath = safe_normpath(linkpath)
            result = self.files().get(linkpath)
        return result

    # API to access dependency information
    def obsoletes(self):
        """Get package Obsoletes as list of
           (name, flags, (epoch, version, release)) tuples."""
        self._gatherDepInfo()
        return self._obsoletes

    def requires(self):
        """Get package Requires as list of
           (name, flags, (epoch, version, release)) tuples."""
        self._gatherDepInfo()
        return self._requires

    def prereq(self):
        """Get package PreReqs as list of
           (name, flags, (epoch, version, release)) tuples."""
        self._gatherDepInfo()
        return self._prereq

    def req_names(self):
        if self._req_names == -1:
            self._req_names = [x[0] for x in self.requires() + self.prereq()]
        return self._req_names

    def check_versioned_dep(self, name, version):
        # try to match name%_isa as well (e.g. "foo(x86-64)", "foo(x86-32)")
        name_re = re.compile('^%s(\(\w+-\d+\))?$' % re.escape(name))
        for d in self.requires() + self.prereq():
            if name_re.match(d[0]):
                if d[1] & rpm.RPMSENSE_EQUAL != rpm.RPMSENSE_EQUAL \
                        or d[2][1] != version:
                    return False
                return True
        return False

    def conflicts(self):
        """Get package Conflicts as list of
           (name, flags, (epoch, version, release)) tuples."""
        self._gatherDepInfo()
        return self._conflicts

    def provides(self):
        """Get package Provides as list of
           (name, flags, (epoch, version, release)) tuples."""
        self._gatherDepInfo()
        return self._provides

    # internal function to gather dependency info used by the above ones
    def _gather_aux(self, header, list, nametag, flagstag, versiontag,
                    prereq = None):
        names = header[nametag]
        flags = header[flagstag]
        versions = header[versiontag]

        if versions:
            for loop in range(len(versions)):
                evr = stringToVersion(versions[loop])
                if prereq is not None and flags[loop] & PREREQ_FLAG:
                    prereq.append((names[loop], flags[loop] & (~PREREQ_FLAG),
                                   evr))
                else:
                    list.append((names[loop], flags[loop], evr))

    def _gatherDepInfo(self):
        if self._requires is None:
            self._requires = []
            self._prereq = []
            self._provides = []
            self._conflicts = []
            self._obsoletes = []

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

    def scriptprog(self, which):
        """Get the specified script interpreter as a string.
           Depending on rpm-python version, the string may or may not include
           interpreter arguments, if any."""
        prog = self[which]
        if prog is None:
            prog = ""
        elif not isinstance(prog, basestring):
            # http://rpm.org/ticket/847#comment:2
            prog = " ".join(prog)
        return prog

def getInstalledPkgs(name):
    """Get list of installed package objects by name."""

    pkgs = []
    ts = rpm.TransactionSet()
    if re.search('[?*]|\[.+\]', name):
        mi = ts.dbMatch()
        mi.pattern("name", rpm.RPMMIRE_GLOB, name)
    else:
        mi = ts.dbMatch("name", name)

    for hdr in mi:
        pkgs.append(InstalledPkg(name, hdr))

    return pkgs

# Class to provide an API to an installed package
class InstalledPkg(Pkg):
    def __init__(self, name, hdr = None):
        if not hdr:
            ts = rpm.TransactionSet()
            mi = ts.dbMatch('name', name)
            if not mi:
                raise KeyError(name)
            try:
                hdr = mi.next()
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
class FakePkg:
    def __init__(self, name):
        self.name = name
        self.arch = None
        self.current_linenum = None

    def cleanup(self):
        pass

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

    is_config    = property(lambda self: self.flags & rpm.RPMFILE_CONFIG)
    is_doc       = property(lambda self: self.flags & rpm.RPMFILE_DOC)
    is_noreplace = property(lambda self: self.flags & rpm.RPMFILE_NOREPLACE)
    is_ghost     = property(lambda self: self.flags & rpm.RPMFILE_GHOST)
    is_missingok = property(lambda self: self.flags & rpm.RPMFILE_MISSINGOK)


if __name__ == '__main__':
    for p in sys.argv[1:]:
        pkg = Pkg(sys.argv[1], tempfile.gettempdir())
        print ('Requires: %s' % pkg.requires())
        print ('Prereq: %s' % pkg.prereq())
        print ('Conflicts: %s' % pkg.conflicts())
        print ('Provides: %s' % pkg.provides())
        print ('Obsoletes: %s' % pkg.obsoletes())
        pkg.cleanup()

# Pkg.py ends here

# Local variables:
# indent-tabs-mode: nil
# py-indent-offset: 4
# End:
# ex: ts=4 sw=4 et
