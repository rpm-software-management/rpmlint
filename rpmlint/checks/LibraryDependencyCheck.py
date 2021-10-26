from pathlib import Path
import stat

from rpmlint.checks import FilesCheck
from rpmlint.checks.AbstractCheck import AbstractCheck
from rpmlint.pkg import FakePkg


class LibraryDependencyCheck(AbstractCheck):
    def __init__(self, config, output):
        super().__init__(config, output)
        self.package_requires = {}
        self.package_so_symlinks = {}
        self.package_so_files = {}
        self.package_arch_mapping = {}

    def check_binary(self, pkg):
        if pkg.is_source:
            return

        is_devel = FilesCheck.devel_regex.search(pkg.name)
        if is_devel:
            self._process_devel_package(pkg, is_devel)
        else:
            self._process_nondevel_package(pkg)

    def _process_devel_package(self, pkg, is_devel):
        self.package_requires[pkg.name] = [req[0] for req in pkg.requires + pkg.prereq]
        self.package_so_symlinks[pkg.name] = []
        self.package_arch_mapping[pkg.name] = pkg.arch

        for pkgfile in pkg.files.values():
            if stat.S_ISLNK(pkgfile.mode) and pkgfile.name.endswith('.so'):
                link = Path(pkgfile.name).parent / pkgfile.linkto
                self.package_so_symlinks[pkg.name].append(str(link))

    def _process_nondevel_package(self, pkg):
        for pkgfile in pkg.files.values():
            if FilesCheck.lib_regex.match(pkgfile.name):
                self.package_so_files[pkgfile.name] = pkg.name

    def after_checks(self):
        for pkgname, so_symlinks in self.package_so_symlinks.items():
            for link in so_symlinks:
                with FakePkg(pkgname) as pkg:
                    pkg.arch = self.package_arch_mapping[pkgname]
                    if link not in self.package_so_files:
                        self.output.add_info('E', pkg, 'no-library-dependency-for', link)
                        break
                    else:
                        definition = self.package_so_files[link]
                        if definition not in self.package_requires[pkgname]:
                            self.output.add_info('E', pkg, 'no-library-dependency-on', definition)
                            break
