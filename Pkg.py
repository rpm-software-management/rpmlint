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

import rpm

from Filter import printWarning


RPMFILE_CONFIG = (1 << 0)
RPMFILE_DOC = (1 << 1)
RPMFILE_DONOTUSE = (1 << 2)
RPMFILE_MISSINGOK = (1 << 3)
RPMFILE_NOREPLACE = (1 << 4)
RPMFILE_SPECFILE = (1 << 5)
RPMFILE_GHOST = (1 << 6)
RPMFILE_LICENSE = (1 << 7)
RPMFILE_README = (1 << 8)

# check if we use a rpm version compatible with 3.0.4
try:
    if rpm.RPMTAG_OLDFILENAMES:
        v304 = 1
except AttributeError:
    v304 = 0

try:
    if rpm.RPMSENSE_SCRIPT_PRE:
        PREREQ_FLAG = rpm.RPMSENSE_PREREQ|rpm.RPMSENSE_SCRIPT_PRE|rpm.RPMSENSE_SCRIPT_POST|rpm.RPMSENSE_SCRIPT_PREUN|rpm.RPMSENSE_SCRIPT_POSTUN
except AttributeError:
    try:
        PREREQ_FLAG = rpm.RPMSENSE_PREREQ
    except:
        #(proyvind): This seems ugly, but then again so does this whole check as well.
        PREREQ_FLAG = False
# check if we use a rpm version compatible with 4.2
v42 = 0
try:
    if rpm.RPMTAG_DISTTAG: # in >= 4.4
        v42 = 1
        #(proyvind): Don't use RPMTAG_OLDFILENAMES with rpm 4.4, especially since
        #            it's put to rest with rpm5.org.
        v304 = 0
except AttributeError:
    try:
        if rpm.RPMTAG_SOURCEPACKAGE: # in 4.2 but not in 4.4.something (6?)
            v42 = 1
    except AttributeError:
        pass

# utilities

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

def getstatusoutput(cmd, stdoutonly = 0):
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

# TODO: is_utf8 could probably be implemented natively without iconv...

def is_utf8(fname):
    cat = 'gzip -dcf'
    if bz2_regex.search(fname): cat = 'bzip2 -dcf'
    if fname.endswith('lzma'): cat = 'lzma -dc'
    # TODO: better shell escaping or sequence based command invocation
    cmd = commands.getstatusoutput('%s "%s" | iconv -f utf-8 -t utf-8 -o /dev/null' % (cat, fname))
    return not cmd[0]

def is_utf8_str(s):
    try:
        s.decode('UTF-8')
    except:
        return 0
    return 1

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
    suffix = ".rpmlint%s" % os.getpid()
    tmpfd, tmpname = tempfile.mkstemp(suffix)
    tmpfile = os.fdopen(tmpfd, 'w')
    return tmpfile, tmpname

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
        if not 'Development/Debug' in groups:
            groups.append('Development/Debug')
            groups.sort()
    return groups

# classes representing package

class Pkg:
    file_regex = re.compile('\.?([^:]+):\s+(.*)')

    def __init__(self, filename, dirname, header = None, is_source = 0):
        self.filename = filename
        self.extracted = 0
        self.dirname = dirname
        self.file_info = None
        self.current_linenum = None
        self._config_files = None
        self._doc_files = None
        self._ghost_files = None
        self._missing_ok_files = None
        self._files = None
        self._requires = None
        self._req_names = -1

        if header:
            self.header = header
            self.is_source = is_source
        else:
            # Create a package object from the file name
            if v42:
                ts = rpm.TransactionSet()
                # Don't check signatures here...
                ts.setVSFlags(rpm._RPMVSF_NOSIGNATURES)
                fd = os.open(filename, os.O_RDONLY)
                try:
                    self.header = ts.hdrFromFdno(fd)
                finally:
                    os.close(fd)
                self.is_source = not self.header[rpm.RPMTAG_SOURCERPM]
            else:
                fd = os.open(filename, os.O_RDONLY)
                try:
                    (self.header, self.is_source) = rpm.headerFromPackage(fd)
                finally:
                    os.close(fd)

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
            self.dirname = '%s/%s.%d' % (self.dirname, os.path.basename(self.filename), os.getpid())
            os.mkdir(self.dirname)
            # TODO: better shell escaping or sequence based command invocation
            command_str = 'rpm2cpio "%s" | (cd "%s"; cpio -id); chmod -R +rX "%s"' % (self.filename, self.dirname, self.dirname)
            cmd = commands.getstatusoutput(command_str)
            self.extracted = 1
            return cmd

    def checkSignature(self):
        return getstatusoutput(('env', 'LC_ALL=C', 'rpm', '-K', self.filename))

    # return the array of info returned by the file command on each file
    def getFilesInfo(self):
        if self.file_info is None:
            self.file_info = []
            lines = commands.getoutput('cd %s ; find . -type f -print0 | LC_ALL=C xargs -0r file' % self.dirName())
            lines = lines.splitlines()
            for l in lines:
                #print l
                res = Pkg.file_regex.search(l)
                if res:
                    self.file_info.append([res.group(1), res.group(2)])
            #print self.file_info
        return self.file_info

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
        self._gatherFilesInfo()
        return self._config_files

    # return the list of noreplace files
    def noreplaceFiles(self):
        if self._noreplace_files is not None:
            return self._noreplace_files
        self._gatherFilesInfo()
        return self._noreplace_files

    # return the list of documentation files
    def docFiles(self):
        if self._doc_files is not None:
            return self._doc_files
        self._gatherFilesInfo()
        return self._doc_files

    # return the list of ghost files
    def ghostFiles(self):
        if self._ghost_files is not None:
            return self._ghost_files
        self._gatherFilesInfo()
        return self._ghost_files

    def missingOkFiles(self):
        if self._missing_ok_files is not None:
            return self._missing_ok_files
        self._gatherFilesInfo()
        return self._missing_ok_files

    # extract information about the files
    def _gatherFilesInfo(self):
        global v304

        self._config_files = []
        self._doc_files = []
        self._noreplace_files = []
        self._ghost_files = []
        self._missing_ok_files = []
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

        # rpm-python < 4.6 does not return a list for this (or FILEDEVICES,
        # FWIW) for packages containing exactly one file
        if not isinstance(inodes, types.ListType):
            inodes = [inodes]

        # Get files according to rpm version
        if v304:
            files = self.header[rpm.RPMTAG_OLDFILENAMES]
            if not files:
                basenames = self.header[rpm.RPMTAG_BASENAMES]
                if basenames:
                    dirnames = self.header[rpm.RPMTAG_DIRNAMES]
                    dirindexes = self.header[rpm.RPMTAG_DIRINDEXES]
                    files = []
                    # The rpmlib or the python module doesn't report a list for RPMTAG_DIRINDEXES
                    # if the list has one element...
                    if isinstance(dirindexes, types.IntType):
                        files.append(dirnames[dirindexes] + basenames[0])
                    else:
                        for idx in range(0, len(dirindexes)):
                            files.append(dirnames[dirindexes[idx]] + basenames[idx])
        else:
            files = self.header[rpm.RPMTAG_FILENAMES]

        if files:
            for idx in range(0, len(files)):
                if flags[idx] & RPMFILE_CONFIG:
                    self._config_files.append(files[idx])
                if flags[idx] & RPMFILE_DOC:
                    self._doc_files.append(files[idx])
                if flags[idx] & RPMFILE_NOREPLACE:
                    self._noreplace_files.append(files[idx])
                if flags[idx] & RPMFILE_GHOST:
                    self._ghost_files.append(files[idx])
                if flags[idx] & RPMFILE_MISSINGOK:
                    self._missing_ok_files.append(files[idx])
                self._files[files[idx]] = (modes[idx], users[idx],
                                           groups[idx], links[idx],
                                           sizes[idx], md5s[idx],
                                           mtimes[idx], rdevs[idx],
                                           langs[idx], inodes[idx])

    def fileLang(self, f):
        return self.files()[f][8]

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
        for d in self.requires() + self.prereq():
            if d[0] == name:
                current_version = d[1]
                if current_version.find(':') > 0:
                    current_version = ''.join(current_version.split(':')[1:])
                if d[2] & rpm.RPMSENSE_EQUAL != rpm.RPMSENSE_EQUAL or current_version != version:
                    return 0
                else:
                    return 1
        return 0

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
            # work around buggy rpm python module that doesn't return a list
            # TODO which rpm-python version is this? seems to work in >= 4.3.3
            if not isinstance(flags, types.ListType):
                flags = [flags]
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
    if v42:
        ts = rpm.TransactionSet()
        if re.search('[?*[]', name):
            tab = ts.dbMatch()
            tab.pattern("name", rpm.RPMMIRE_GLOB, name)
        else:
            tab = ts.dbMatch("name", name)
        if not tab:
            raise KeyError(name)
        for hdr in tab:
            pkgs.append(InstalledPkg(name, hdr))
    else:
        db = rpm.opendb()
        ixs = db.findbyname(name)
        if not ixs:
            del db
            raise KeyError(name)
        for ix in ixs:
            pkgs.append(InstalledPkg(name, db[ix]))
        del db
    return pkgs

# Class to provide an API to an installed package
class InstalledPkg(Pkg):
    def __init__(self, name, h = None):
        if h:
            Pkg.__init__(self, name, '/', h)
        else:
            if v42:
                ts = rpm.TransactionSet()
                tab = ts.dbMatch('name', name)
                if not tab:
                    raise KeyError(name)
                theHdr = tab.next()
            else:
                db = rpm.opendb()
                tab = db.findbyname(name)
                if not tab:
                    del db
                    raise KeyError(name)
                theHdr = db[tab[0]]
                del db
            Pkg.__init__(self, name, '/', theHdr)
        self.extracted = 1
        # create a fake filename to satisfy some checks on the filename
        self.filename = '%s-%s-%s.%s.rpm' % (self.name, self[rpm.RPMTAG_VERSION], self[rpm.RPMTAG_RELEASE], self[rpm.RPMTAG_ARCH])

    def cleanup(self):
        pass

    def checkSignature(self):
        return (0, 'fake: pgp md5 OK')

    # return the array of info returned by the file command on each file
    def getFilesInfo(self):
        if self.file_info is None:
            self.file_info = []
            cmd = ['env', 'LC_ALL=C', 'file']
            cmd.extend(self.files())
            sts, lines = getstatusoutput(cmd)
            #print lines
            lines = lines.splitlines()
            for l in lines:
                #print l
                res = Pkg.file_regex.search(l)
                if res:
                    self.file_info.append([res.group(1), res.group(2)])
            #print self.file_info
        return self.file_info

# Class to provide an API to a "fake" package, eg. for specfile-only checks
class FakePkg:
    def __init__(self, name):
        self.name = name
        self.arch = None

    def cleanup(self):
        pass

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
