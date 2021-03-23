import os
import stat

from rpmlint.checks.AbstractCheck import AbstractCheck


class FileMeta:
    def __init__(self, pkgfile):
        self.path = pkgfile.name
        self.pkgfile = pkgfile
        self.owner = pkgfile.user
        self.group = pkgfile.group
        self.mode = stat.filemode(pkgfile.mode)
        self.device_minor = os.minor(pkgfile.rdev)
        self.device_major = os.major(pkgfile.rdev)

    def get_validation_error(self, entry, prefix):
        for key, value in entry.items():
            file_value = getattr(self, key)
            if value != file_value:
                return ((f'{prefix}-mismatched-attrs', self.path, f'expected "{key}": {value}, has: {file_value}'))
        return None

    def __repr__(self):
        return f'FileMeta({self.pkgfile.name} = {self.owner}:{self.group} {self.mode} {self.device_minor},{self.device_major})'


class FileMetadataCheck(AbstractCheck):
    def __init__(self, config, output):
        super().__init__(config, output)

    def verify_whitelists(self, keys):
        for item in self.whitelists:
            if 'package' not in item:
                raise KeyError("FileMetadataCheck: missing 'package' key")
            for file_entry in item['files']:
                for key in keys:
                    if key not in file_entry:
                        raise KeyError(f"FileMetadataCheck: missing '{key}' in files")

    def _verify_package_whitelist(self, whitelist, files):
        errors = []
        for filename, meta in files.items():
            file_entry = next((e for e in whitelist['files'] if e['path'] == filename), None)
            if file_entry:
                err = meta.get_validation_error(file_entry, self.prefix)
                if err:
                    errors.append(err)
            else:
                errors.append((f'{self.prefix}-unauthorized-file', filename, None))
        return errors

    def check_files(self, pkg, files):
        # start with unauthorized for all files
        best_errors = self._verify_package_whitelist({'files': []}, files)

        for whitelist in self.whitelists:
            if whitelist['package'] == pkg.name:
                errors = self._verify_package_whitelist(whitelist, files)
                if len(errors) <= len(best_errors):
                    best_errors = errors

        if best_errors:
            for message, filename, error_detail in best_errors:
                self.output.add_info('E', pkg, message, filename, error_detail)
