# -*- coding: utf-8 -*-
#############################################################################
# File          : Pkg.py
# Package       : rpmlint
# Author        : Frederic Lepied
# Created on    : Tue Sep 28 07:18:06 1999
# Version       : $Id$
# Purpose       : provide an API to handle a rpm package either by accessing
#                 the rpm file or by accessing the files contained inside.
#############################################################################

import commands
import os
import re
import stat
import sys
import tempfile
import types
import subprocess

try:
    import magic
    # TODO: magic.MAGIC_COMPRESS when PkgFile gets decompress support.
    _magic = magic.open(magic.MAGIC_NONE)
    _magic.load()
except:
    _magic = None
import rpm

from Filter import printWarning


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
        return res.group(1) + value + substitute_shell_vars(res.group(3), script)
    else:
        return val

def getstatusoutput(cmd, stdoutonly = False):
    '''A version of commands.getstatusoutput() which can take cmd as a
       sequence, thus making it potentially more secure.'''
    if stdoutonly:
        proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, close_fds=True)
    else:
        proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, close_fds=True)
    proc.stdin.close()
    text = proc.stdout.read()
    sts = proc.wait()
    if sts is None: sts = 0
    if text.endswith('\n'):
        text = text[:-1]
    return sts, text

bz2_regex = re.compile('\.t?bz2?$')
xz_regex = re.compile('\.(t[xl]z|xz|lzma)$')

# TODO: is_utf8 could probably be implemented natively without iconv...

def is_utf8(fname):
    cat = 'gzip -dcf'
    if bz2_regex.search(fname): cat = 'bzip2 -dcf'
    elif xz_regex.search(fname): cat = 'xz -dc'
    # TODO: better shell escaping or sequence based command invocation
    cmd = commands.getstatusoutput('%s "%s" | iconv -f utf-8 -t utf-8 -o /dev/null' % (cat, fname))
    return not cmd[0]

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

def get_default_valid_rpmgroups(filename = ""):
    """ Get the default rpm group from filename, or from the rpm package if no
    filename is given"""
    groups = []
    if not filename:
        p = InstalledPkg('rpm')
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
        groups.sort()
    return groups

# from yum 3.2.23, rpmUtils.miscutils
def compareEVR((e1, v1, r1), (e2, v2, r2)):
    # return 1: a is newer than b
    # 0: a and b are the same version
    # -1: b is newer than a
    e1 = str(e1)
    v1 = str(v1)
    r1 = str(r1)
    e2 = str(e2)
    v2 = str(v2)
    r2 = str(r2)
    rc = rpm.labelCompare((e1, v1, r1), (e2, v2, r2))
    return rc

# from yum 3.2.23, rpmUtils.miscutils with some rpmlint modifications
def rangeCompare(reqtuple, provtuple):
    """returns true if provtuple satisfies reqtuple"""
    (reqn, reqf, (reqe, reqv, reqr)) = reqtuple
    (n, f, (e, v, r)) = provtuple
    if reqn != n:
        return 0

    # rpmlint modification: flags=0 (in addition to None) satisfies everything
    if not f or not reqf:
        return 1

    # and you thought we were done having fun
    # if the requested release is left out then we have
    # to remove release from the package prco to make sure the match
    # is a success - ie: if the request is EQ foo 1:3.0.0 and we have 
    # foo 1:3.0.0-15 then we have to drop the 15 so we can match
    if reqr is None:
        r = None
    if reqe is None:
        e = None
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
            if f in ['LE', 10]:
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

    return 0

# from yum 3.2.23, rpmUtils.miscutils
def formatRequire (name, version, flags):
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
            if version:
                s = "%s %s" %(s, version)
    return s

# from yum 3.2.23, rpmUtils.miscutils
def stringToVersion(verstring):
    if verstring in [None, '']:
        return (None, None, None)
    i = verstring.find(':')
    if i != -1:
        try:
            epoch = str(long(verstring[:i]))
        except ValueError:
            # look, garbage in the epoch field, how fun, kill it
            epoch = '0' # this is our fallback, deal
    else:
        epoch = '0'
    j = verstring.find('-')
    if j != -1:
        if verstring[i + 1:j] == '':
            version = None
        else:
            version = verstring[i + 1:j]
        release = verstring[j + 1:]
    else:
        if verstring[i + 1:] == '':
            version = None
        else:
            version = verstring[i + 1:]
        release = None
    return (epoch, version, release)

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
        s = os.stat(self.dirname)
        if not stat.S_ISDIR(s[stat.ST_MODE]):
            sys.stderr.write('unable to access dir %s\n' % self.dirname)
            return None
        else:
            self.dirname = tempfile.mkdtemp(
                prefix = 'rpmlint.%s.' % os.path.basename(self.filename),
                dir = self.dirname)
            # TODO: better shell escaping or sequence based command invocation
            command_str = 'rpm2cpio "%s" | (cd "%s"; cpio -id); chmod -R +rX "%s"' % (self.filename, self.dirname, self.dirname)
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
                printWarning(self, 'read-error', filename, e)
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
        deps = self.header[rpm.RPMTAG_FILEREQUIRE]
        files = self.header[rpm.RPMTAG_FILENAMES]
        magics = self.header[rpm.RPMTAG_FILECLASS]

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
                pkgfile.deps = deps[idx]
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
                self._files[pkgfile.name] = pkgfile

    # API to access dependency information
    def obsoletes(self):
        self._gatherDepInfo()
        return self._obsoletes

    def requires(self):
        self._gatherDepInfo()
        return self._requires

    def prereq(self):
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
                current_version = d[1]
                if current_version.find(':') > 0:
                    current_version = ''.join(current_version.split(':')[1:])
                if d[2] & rpm.RPMSENSE_EQUAL != rpm.RPMSENSE_EQUAL \
                        or current_version != version:
                    return False
                return True
        return False

    def conflicts(self):
        self._gatherDepInfo()
        return self._conflicts

    def provides(self):
        self._gatherDepInfo()
        return self._provides

    # internal function to gather dependency info used by the above ones
    def _gather_aux(self, header, list, nametag, versiontag, flagstag, prereq = None):
        names = header[nametag]
        versions = header[versiontag]
        flags = header[flagstag]

        if versions:
            for loop in range(len(versions)):
                if prereq is not None and flags[loop] & PREREQ_FLAG:
                    prereq.append((names[loop], versions[loop], flags[loop] & (~PREREQ_FLAG)))
                else:
                    list.append((names[loop], versions[loop], flags[loop]))

    def _gatherDepInfo(self):
        if self._requires is None:
            self._requires = []
            self._prereq = []
            self._provides = []
            self._conflicts = []
            self._obsoletes = []

            self._gather_aux(self.header, self._requires,
                             rpm.RPMTAG_REQUIRENAME,
                             rpm.RPMTAG_REQUIREVERSION,
                             rpm.RPMTAG_REQUIREFLAGS,
                             self._prereq)
            self._gather_aux(self.header, self._conflicts,
                             rpm.RPMTAG_CONFLICTNAME,
                             rpm.RPMTAG_CONFLICTVERSION,
                             rpm.RPMTAG_CONFLICTFLAGS)
            self._gather_aux(self.header, self._provides,
                             rpm.RPMTAG_PROVIDENAME,
                             rpm.RPMTAG_PROVIDEVERSION,
                             rpm.RPMTAG_PROVIDEFLAGS)
            self._gather_aux(self.header, self._obsoletes,
                             rpm.RPMTAG_OBSOLETENAME,
                             rpm.RPMTAG_OBSOLETEVERSION,
                             rpm.RPMTAG_OBSOLETEFLAGS)

def getInstalledPkgs(name):
    """Get list of installed package objects by name."""

    pkgs = []
    ts = rpm.TransactionSet()
    if re.search('[?*]|\[.+\]', name):
        mi = ts.dbMatch()
        mi.pattern("name", rpm.RPMMIRE_GLOB, name)
    else:
        mi = ts.dbMatch("name", name)
    if not mi:
        raise KeyError(name)

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
        self.filename = '%s-%s-%s.%s.rpm' % (self.name, self[rpm.RPMTAG_VERSION], self[rpm.RPMTAG_RELEASE], self[rpm.RPMTAG_ARCH])

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
        self.deps = ''
        self.lang = ''
        self.magic = ''

    # TODO: decompression support

    is_config    = property(lambda self: self.flags & rpm.RPMFILE_CONFIG)
    is_doc       = property(lambda self: self.flags & rpm.RPMFILE_DOC)
    is_noreplace = property(lambda self: self.flags & rpm.RPMFILE_NOREPLACE)
    is_ghost     = property(lambda self: self.flags & rpm.RPMFILE_GHOST)
    is_missingok = property(lambda self: self.flags & rpm.RPMFILE_MISSINGOK)


if __name__ == '__main__':
    for p in sys.argv[1:]:
        pkg = Pkg(sys.argv[1], tempfile.gettempdir())
        sys.stdout.write('Requires: %s\n' % pkg.requires())
        sys.stdout.write('Prereq: %s\n' % pkg.prereq())
        sys.stdout.write('Conflicts: %s\n' % pkg.conflicts())
        sys.stdout.write('Provides: %s\n' % pkg.provides())
        sys.stdout.write('Obsoletes: %s\n' % pkg.obsoletes())
        pkg.cleanup()

# Pkg.py ends here

# Local variables:
# indent-tabs-mode: nil
# py-indent-offset: 4
# End:
# ex: ts=4 sw=4 et
