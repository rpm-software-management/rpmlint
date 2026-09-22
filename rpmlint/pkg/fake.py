import hashlib
import io
import os
from pathlib import Path, PurePath
import re
import shutil
import stat
import tempfile

import rpm
from rpmlint.pkg.base import AbstractPkg
from rpmlint.pkg.utils import parse_deps, versionToString
from rpmlint.pkgfile import PkgFile


class FakeHeader(dict):
    def sprintf(self, expr):
        """
        Replaces expressions like %{} with actual package
        """

        tagre = re.compile(r'%{([^}]*)}')
        for tag in tagre.findall(expr):
            expr = expr.replace(f'%{tag}', self[f'RPMTAG_{tag}'])
        return expr

    def __missing__(self, key):
        try:
            key = getattr(rpm, key)
        except (TypeError, KeyError):
            raise KeyError

        if key not in self:
            raise KeyError

        return self[key]


# Class to provide an API to a 'fake' package, eg. for specfile-only checks
class FakePkg(AbstractPkg):
    _autoheaders = [
        'requires',
        'conflicts',
        'provides',
        'obsoletes',
        'recommends',
        'suggests',
        'enhances',
        'supplements',
    ]

    def __init__(self, name, is_source=False):
        self.timers = {'ExtractRpm': 0, 'libmagic': 0}
        self.name = str(name)
        self.filename = f'{name}.rpm'
        self.arch = None
        self.current_linenum = None
        self.dirname = None
        self.is_source = False

        # files are dictionary where key is name of a file
        self.files = {}
        self.ghost_files = {}

        # header is a dictionary to mock rpm metadata
        self.header = FakeHeader()
        for i in self._autoheaders:
            # the header name wihtout the ending 's'
            tagname = i[:-1].upper()
            self.header[getattr(rpm, f'RPMTAG_{tagname}NAME')] = []
            self.header[getattr(rpm, f'RPMTAG_{tagname}FLAGS')] = []
            self.header[getattr(rpm, f'RPMTAG_{tagname}VERSION')] = []
        self.header[rpm.RPMTAG_FILENAMES] = []

    def add_file(self, path, name):
        pkgfile = PkgFile(name)
        pkgfile.path = path
        self.files[name] = pkgfile
        return pkgfile

    def _mock_file(self, path, attrs):
        metadata = None
        if attrs.get('create_dirs', False):
            for i in PurePath(path).parents[:attrs.get('include_dirs', -1)]:
                self.add_dir(str(i))
        metadata = attrs.get('metadata', None)

        if attrs.get('is_dir', False):
            self.add_dir(path, metadata=metadata)
            return

        content = ''
        if 'content-path' in attrs:
            content = open(attrs['content-path'], 'rb')
        elif 'content' in attrs:
            content = attrs['content']

        if 'linkto' in attrs:
            self.add_symlink_to(path, attrs['linkto'])
        else:
            self.add_file_with_content(path, content, metadata=metadata)
        self.header[rpm.RPMTAG_FILENAMES].append(path)

        if 'content-path' in attrs:
            content.close()

    def create_files(self, files):
        """
        This is a helper method to create files(real files); not PkgFile
        objects.
        """

        # files can be just a list
        if isinstance(files, (list, tuple)):
            for path in files:
                self._mock_file(path, {})
        # list of files with attributes and content
        elif isinstance(files, dict):
            for path, file in files.items():
                self._mock_file(path, file)

    def add_dir(self, path, metadata=None):
        name = path
        pkgdir = PkgFile(name)
        pkgdir.magic = 'directory'

        path = os.path.join(self.dir_name(), path.lstrip('/'))
        os.makedirs(Path(path), exist_ok=True)
        pkgdir.inode = os.stat(Path(path)).st_ino

        pkgdir.path = path
        self.files[name] = pkgdir

        if metadata:
            for k, v in metadata.items():
                setattr(pkgdir, k, v)

        return pkgdir

    def add_file_with_content(self, name, content, metadata=None, perms=0o644, **flags):
        """
        Add file to the FakePkg and fill the file with provided
        string content.
        """
        path = os.path.join(self.dir_name(), name.lstrip('/'))
        pkg_file = PkgFile(name)
        pkg_file.path = path
        pkg_file.mode = stat.S_IFREG | perms
        pkg_file.user = 'root'
        pkg_file.group = 'root'
        self.files[name] = pkg_file

        # create files in filesystem
        os.makedirs(Path(path).parent, exist_ok=True)

        if isinstance(content, str):
            content = content.encode('utf-8', errors='ignore')

        with open(Path(path), 'wb') as out:
            # file like content
            if isinstance(content, io.IOBase):
                shutil.copyfileobj(content, out)
            else:
                out.write(content)

        # Generating md5 hash values for real files:
        pkg_file.md5 = self.md5_checksum(Path(path))
        pkg_file.size = os.path.getsize(Path(path))
        pkg_file.inode = os.stat(Path(path)).st_ino
        pkg_file.magic = self._calc_magic(pkg_file)

        if metadata:
            for k, v in metadata.items():
                setattr(pkg_file, k, v)
        for key, value in flags.items():
            setattr(pkg_file, key, value)

    def initiate_files_base_data(self):
        """ This method is called after adding metadata of each file """
        self.config_files = [x.name for x in self.files.values() if x.is_config]
        self.doc_files = [x.name for x in self.files.values() if x.is_doc]
        self.ghost_files = [x.name for x in self.files.values() if x.is_ghost]
        self.noreplace_files = [x.name for x in self.files.values() if x.is_noreplace]
        self.missingok_files = [x.name for x in self.files.values() if x.is_missingok]

    def add_header(self, header):
        for k, v in header.items():
            if k in self._autoheaders:
                # the header name wihtout the ending 's'
                tagname = k[:-1].upper()
                for i in v:
                    name, flags, version = parse_deps(i)[0]
                    version = versionToString(version)
                    self.header[getattr(rpm, f'RPMTAG_{tagname}NAME')].append(name)
                    self.header[getattr(rpm, f'RPMTAG_{tagname}FLAGS')].append(flags)
                    self.header[getattr(rpm, f'RPMTAG_{tagname}VERSION')].append(version)
                continue

            key = getattr(rpm, f'RPMTAG_{k}'.upper())
            self.header[key] = v

            if key == rpm.RPMTAG_ARCH:
                self.arch = v

        (self.requires, self.prereq, self.provides, self.conflicts,
         self.obsoletes, self.recommends, self.suggests, self.enhances,
         self.supplements) = self._gather_dep_info()

        self.req_names = [x[0] for x in self.requires + self.prereq]

    def add_dependency(self, dep):
        name, flags, version = parse_deps(dep)[0]
        version = versionToString(version)
        self.header[rpm.RPMTAG_REQUIRESNAME].append(name)
        self.header[rpm.RPMTAG_REQUIRESFLAGS].append(flags)
        self.header[rpm.RPMTAG_REQUIRESVERSION].append(version)

        _requires = []
        _prereq = []
        self.requires, self.prereq = self._gather_aux(self.header, _requires,
                                                      rpm.RPMTAG_REQUIRENAME,
                                                      rpm.RPMTAG_REQUIREFLAGS,
                                                      rpm.RPMTAG_REQUIREVERSION,
                                                      _prereq)

        self.req_names = [x[0] for x in self.requires + self.prereq]

    def add_symlink_to(self, name, target):
        """
        Add symlink to name file which path is related to name.
        Eg. name == '/etc/foo' and target == '../bar' creates a symlink file
        /etc/bar that points to /etc/foo.
        """
        pkg_file = PkgFile(name)
        pkg_file.mode = stat.S_IFLNK
        pkg_file.linkto = target
        pkg_file.user = 'root'
        pkg_file.group = 'root'
        self.files[name] = pkg_file

    def add_ghost(self, name):
        pkg_file = PkgFile(name)
        pkg_file.flags |= rpm.RPMFILE_GHOST
        self.files[name] = pkg_file
        self.ghost_files[name] = pkg_file

    def dir_name(self):
        if not self.dirname:
            self.__tmpdir = tempfile.TemporaryDirectory(prefix='rpmlint.%s.' % Path(self.name).name)
            self.dirname = self.__tmpdir.name
        return self.dirname

    def md5_checksum(self, file_name):
        md5_hash = hashlib.md5()
        with open(file_name, 'rb') as f:
            for byte_block in iter(lambda: f.read(4096), b''):
                md5_hash.update(byte_block)
        return md5_hash.hexdigest()

    def cleanup(self):
        if self.dirname:
            self.__tmpdir.cleanup()

    def get_core_reqs(self):
        core_reqs = []
        return core_reqs

    # access the tags like an array
    def __getitem__(self, key):
        return self.header.get(key, None)
