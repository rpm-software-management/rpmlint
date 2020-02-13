import rpm


class PkgFile(object):

    __slots__ = ['name', 'path', 'flags', 'mode', 'user', 'group', 'linkto',
                 'size', 'md5', 'mtime', 'rdev', 'inode', 'requires', 'provides',
                 'lang', 'magic', 'filecaps']

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

    @property
    def is_config(self):
        return self.flags & rpm.RPMFILE_CONFIG

    @property
    def is_doc(self):
        return self.flags & rpm.RPMFILE_DOC

    @property
    def is_noreplace(self):
        return self.flags & rpm.RPMFILE_NOREPLACE

    @property
    def is_ghost(self):
        return self.flags & rpm.RPMFILE_GHOST

    @property
    def is_missingok(self):
        return self.flags & rpm.RPMFILE_MISSINGOK
