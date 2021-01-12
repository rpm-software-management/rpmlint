from rpmlint.checks.FileMetadataCheck import FileMeta, FileMetadataCheck


class DeviceFilesCheck(FileMetadataCheck):
    def __init__(self, config, output):
        super().__init__(config, output)
        self.whitelists = self.config.configuration['DeviceFilesWhitelist']
        self.verify_whitelists(['path', 'owner', 'group', 'mode', 'device_minor', 'device_major'])
        self.prefix = 'device'

    def check_binary(self, pkg):
        files = [FileMeta(pfile) for pfile in pkg.files.values()]
        # select only block and character devices, ignore symlinks
        files = {f.path: f for f in files if f.mode[0] in 'bc'}
        self.check_files(pkg, files)
