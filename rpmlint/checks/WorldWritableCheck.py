from rpmlint.checks.FileMetadataCheck import FileMeta, FileMetadataCheck


class WorldWritableCheck(FileMetadataCheck):
    def __init__(self, config, output):
        super().__init__(config, output)
        self.whitelists = self.config.configuration['WorldWritableWhitelist']
        self.verify_whitelists(['path', 'owner', 'group', 'mode'])
        self.prefix = 'world-writable'

    def check_binary(self, pkg):
        files = [FileMeta(pfile) for pfile in pkg.files.values()]
        # select any world-writable files except device files and symlinks
        files = {f.path: f for f in files if f.mode[0] not in 'bcl' and f.mode[-2] == 'w'}
        self.check_files(pkg, files)
