#############################################################################
# File		: Pkg.py
# Package	: rpmlint
# Author	: Frederic Lepied
# Created on	: Tue Sep 28 07:18:06 1999
# Version	: $Id$
# Purpose	: provide an API to handle a rpm package either by accessing
#		the rpm file or by accessing the files contained inside.
#############################################################################

import os
import rpm
import os.path
import stat
import commands
import re
import string
import types

RPMFILE_CONFIG=(1 << 0)
RPMFILE_DOC=(1 << 1)
RPMFILE_DONOTUSE=(1 << 2)
RPMFILE_MISSINGOK=(1 << 3)
RPMFILE_NOREPLACE=(1 << 4)
RPMFILE_SPECFILE=(1 << 5)
RPMFILE_GHOST=(1 << 6)
RPMFILE_LICENSE=(1 << 7)
RPMFILE_README=(1 << 8)

# check if we use a rpm version compatible with 3.0.4
try:
    if rpm.RPMTAG_OLDFILENAMES:
        v304=1
except AttributeError:
    v304=0

# check if we use a rpm version compatible with 4.2
try:
    if rpm.RPMTAG_SOURCEPACKAGE:
        v42=1
except AttributeError:
    v42=0
    
# utilities

def grep(regex, filename):
    fd=open(filename, 'r')
    ret=0
    if fd:
        reg=re.compile(regex)
        
        for line in fd.readlines():
            if reg.search(line):
                ret=1
                break
        fd.close()
    else:
        print 'unable to open', filename
    return ret

def shell_var_value(var, script):
    assign_regex=re.compile(re.escape(var) + '\s*=\s*(.+)\s*(#.*)*$',
                            re.MULTILINE)
    res=assign_regex.search(script)
    if res:
        return substitute_shell_vars(res.group(1), script)
    else:
        return None

var_regex=re.compile('^(.*)\${?([^}]+)}?(.*)$')

def substitute_shell_vars(val, script):
    res=var_regex.search(val)
    if res:
        value=shell_var_value(res.group(2), script)
        if not value:
            value=''
        return res.group(1) + value + substitute_shell_vars(res.group(3), script)
    else:
        return val

# classes representing package

class Pkg:
    file_regex=re.compile('(?:\.)?([^:]+):\s+(.*)')

    def __init__(self, filename, dirname, header=None, is_source=0):
	self.filename=filename
	self.extracted=0
	self.dirname=dirname
	self.file_info=None
	self._config_files=None
	self._doc_files=None
	self._ghost_files=None
	self._files=None
	self.required=None
        self._req_names=-1
        
        if header:
            self.header=header
            self.is_source=is_source
        else:
            # Create a package object from the file name
            if v42:
                ts=rpm.TransactionSet()
                # Don't check signatures here...
                ts.setVSFlags(rpm._RPMVSF_NOSIGNATURES)
                fd=os.open(filename, os.O_RDONLY)
                self.header=ts.hdrFromFdno(fd)
                os.close(fd)
                if self.header[rpm.RPMTAG_SOURCEPACKAGE]:
                    self.is_source=1
                else:
                    self.is_source=0
            else:
                fd=os.open(filename, os.O_RDONLY)
                (self.header, self.is_source)=rpm.headerFromPackage(fd)
                os.close(fd)

        self._lang_files=None

	self.name=self.header[rpm.RPMTAG_NAME]

    # Return true if the package is a source package
    def isSource(self):
	return self.is_source

    # Return true if the package is a nosource package.
    # NoSource files are ghosts in source packages.
    def isNoSource(self):
        return self.is_source and self.ghostFiles()

    # access the tags like an array
    def __getitem__(self, key):
	val = self.header[key]
        if val == []:
            return None
        else:
            return val

    # return the name of the directory where the package is extracted
    def dirName(self):
	if not self.extracted:
	    self._extract()
	return self.dirname

    # handle the extract phasis
    def _extract(self):
	s=os.stat(self.dirname)
        if not stat.S_ISDIR(s[stat.ST_MODE]):
            print 'unable to access dir', self.dirname
            return None
        else:
            self.dirname = '%s/%s.%d' % (self.dirname, os.path.basename(self.filename), os.getpid())
            os.mkdir(self.dirname)
            str='rpm2cpio %s | (cd %s; cpio -id); chmod -R +rX %s' % (self.filename, self.dirname, self.dirname)
            cmd=commands.getstatusoutput(str)
	    self.extracted=1
            return cmd
        
    def checkSignature(self):
        return commands.getstatusoutput('rpm -K ' + self.filename)
    
    # return the array of info returned by the file command on each file
    def getFilesInfo(self):
	if self.file_info == None:
	    self.file_info=[]
	    lines=commands.getoutput('cd %s; find . -type f -print0 | xargs -0r file' % (self.dirName()))
	    lines=string.split(lines, '\n')
	    for l in lines:
		#print l
		res=Pkg.file_regex.search(l)
		if res:
		    self.file_info.append([res.group(1), res.group(2)])
	    #print self.file_info
	return self.file_info

    # remove the extracted files from the package
    def cleanup(self):
	if self.extracted:
	    commands.getstatusoutput('rm -rf ' + self.dirname)

    # return the associative array indexed on file names with
    # the values as: (file perm, file owner, file group, file link to)
    def files(self):
	if self._files != None:
	    return self._files
	self._gatherFilesInfo()
	return self._files

    # return the list of config files
    def configFiles(self):
	if self._config_files != None:
	    return self._config_files
	self._gatherFilesInfo()
	return self._config_files

    # return the list of noreplace files
    def noreplaceFiles(self):
	if self._noreplace_files != None:
	    return self._noreplace_files
	self._gatherFilesInfo()
	return self._noreplace_files

    # return the list of documentation files
    def docFiles(self):
	if self._doc_files != None:
	    return self._doc_files
	self._gatherFilesInfo()
	return self._doc_files

    # return the list of ghost files
    def ghostFiles(self):
	if self._ghost_files != None:
	    return self._ghost_files
	self._gatherFilesInfo()
	return self._ghost_files

    # extract information about the files
    def _gatherFilesInfo(self):
        global v304
        
	self._config_files=[]
	self._doc_files=[]
	self._noreplace_files=[]
	self._ghost_files=[]
	self._files={}
        self._files_array=[]
	flags=self.header[rpm.RPMTAG_FILEFLAGS]
	modes=self.header[rpm.RPMTAG_FILEMODES]
	users=self.header[rpm.RPMTAG_FILEUSERNAME]
	groups=self.header[rpm.RPMTAG_FILEGROUPNAME]
	links=self.header[rpm.RPMTAG_FILELINKTOS]
	sizes=self.header[rpm.RPMTAG_FILESIZES]
	md5s=self.header[rpm.RPMTAG_FILEMD5S]
        mtimes=self.header[rpm.RPMTAG_FILEMTIMES]
        rdevs=self.header[rpm.RPMTAG_FILERDEVS]
        # Get files according to rpm version
        if v304:
            files=self.header[rpm.RPMTAG_OLDFILENAMES]
            if files == None:
                basenames=self.header[rpm.RPMTAG_BASENAMES]
                if basenames:
                    dirnames=self.header[rpm.RPMTAG_DIRNAMES]
                    dirindexes=self.header[rpm.RPMTAG_DIRINDEXES]
                    files=[]
                    # The rpmlib or the python module doesn't report a list for RPMTAG_DIRINDEXES
                    # if the list has one element...
                    if type(dirindexes) == types.IntType:
                        files.append(dirnames[dirindexes] + basenames[0])
                    else:
                        for idx in range(0, len(dirindexes)):
                            files.append(dirnames[dirindexes[idx]] + basenames[idx])
        else:
            files=self.header[rpm.RPMTAG_FILENAMES]

	if files:
            self._files_array=files
	    for idx in range(0, len(files)):
		if flags[idx] & RPMFILE_CONFIG:
		    self._config_files.append(files[idx])
		if flags[idx] & RPMFILE_DOC:
		    self._doc_files.append(files[idx])
		if flags[idx] & RPMFILE_NOREPLACE:
		    self._noreplace_files.append(files[idx])
		if flags[idx] & RPMFILE_GHOST:
		    self._ghost_files.append(files[idx])
		self._files[files[idx]]=(modes[idx], users[idx],
					 groups[idx], links[idx],
                                         sizes[idx], md5s[idx],
                                         mtimes[idx], rdevs[idx])
                
    def langFiles(self):
        if self._lang_files == None:
            self._lang_files={}
            array=self.header[rpm.RPMTAG_FILELANGS]
            if array:
                for idx in range(0, len(array)):
                    self._lang_files[self._files_array[idx]] = array[idx]
                    
        return self._lang_files

    def fileLang(self, f):
        return self.langFiles()[f]

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
            self._req_names = map(lambda x: x[0], self.requires() + self.prereq())
        return self._req_names

    def check_versioned_dep(self, name, version):
        for d in self.requires()+self.prereq():
            if d[0] == name:
                current_version=d[1]
                if current_version.index(':'):
		    current_version=''.join(current_version.split(':')[1:])
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
    def _gather_aux(self, header, list, nametag, versiontag, flagstag, prereq=None):
        names = header[nametag]
        versions = header[versiontag]
        flags = header[flagstag]
        
        if versions:
            # workaroung buggy rpm python module that doesn't return a list
            if type(flags) != types.ListType:
                flags=[flags]
            for loop in range(len(versions)):
                if prereq != None and flags[loop] & rpm.RPMSENSE_PREREQ:
                    prereq.append((names[loop], versions[loop], flags[loop] & (not rpm.RPMSENSE_PREREQ)))
                else:
                    list.append((names[loop], versions[loop], flags[loop]))
                        
        
    def _gatherDepInfo(self):
        if self.required == None:
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

# Class to provide an API to an installed package
class InstalledPkg(Pkg):
    def __init__(self, name, h=None):
        if h:
            Pkg.__init__(self, name, '/', h)
        else:
            if v42:
                ts = rpm.TransactionSet()
                tab = ts.dbMatch('name', name)
                if not tab:
                    raise KeyError, name
                theHdr = tab.next()
            else:
                db = rpm.opendb()
                tab = db.findbyname(name)
                if not tab:
                    del db
                    raise KeyError, name
                theHdr = db[tab[0]]
                del db
            Pkg.__init__(self, name, '/', theHdr)
        self.extracted = 1
        # create a fake filename to satisfy some checks on the filename
        self.filename = '%s-%s-%s.%s.rpm' % (self[rpm.RPMTAG_NAME], self[rpm.RPMTAG_VERSION], self[rpm.RPMTAG_RELEASE], self[rpm.RPMTAG_ARCH])
        
    def cleanup(self):
        pass

    def checkSignature(self):
        return (0, 'fake: pgp md5 OK')

    # return the array of info returned by the file command on each file
    def getFilesInfo(self):
	if self.file_info == None:
	    self.file_info=[]
            cmd='file'
            for f in self.files().keys():
                cmd=cmd + ' ' + f
            lines=commands.getoutput(cmd)
            #print lines
	    lines=string.split(lines, '\n')
	    for l in lines:
		#print l
		res=Pkg.file_regex.search(l)
		if res:
		    self.file_info.append([res.group(1), res.group(2)])
            #print self.file_info
	return self.file_info

if __name__ == '__main__':
    import sys
    for p in sys.argv[1:]:
        pkg=Pkg(sys.argv[1], '/tmp')
        print 'Requires:', pkg.requires()
        print 'Prereq:', pkg.prereq()
        print 'Conflicts:', pkg.conflicts()
        print 'Provides:', pkg.provides()
        print 'Obsoletes:', pkg.obsoletes()
        pkg.cleanup()
    
# Pkg.py ends here
