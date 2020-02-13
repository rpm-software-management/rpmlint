from pathlib import Path
import stat

import rpm
from rpmlint.checks.AbstractCheck import AbstractCheck
from rpmlint.helpers import byte_to_string


class DocCheck(AbstractCheck):
    """
    Package documentation checks.
    """

    def check_binary(self, pkg):
        if not pkg.doc_files:
            return

        self._check_executable_docs(pkg)
        self._check_doc_file_dependencies(pkg)
        self._check_unwanted_files(pkg)

        if not self._ignore_pkg(pkg.name):
            self._check_huge_docs(pkg)

    @staticmethod
    def _ignore_pkg(name):
        if name.startswith('bundle-') or '-devel' in name or '-doc' in name:
            return True
        return False

    def _check_executable_docs(self, pkg):
        """
        Check if the documentation in the package is executable and print an
        error if it is.
        """
        for f in pkg.doc_files:
            mode = pkg.files[f].mode
            if not stat.S_ISREG(mode) or not mode & 0o111:
                continue
            path = Path(f)
            extensions = ['.txt', '.gif', '.jpg', '.html', '.pdf', '.ps', '.pdf.gz', '.ps.gz']
            if path.suffix in extensions:
                self.output.add_info('E', pkg, 'executable-docs', f)

            for name in ['README', 'NEWS', 'COPYING', 'AUTHORS', 'LICENCE', 'LICENSE']:
                if path.name.lower() == name.lower():
                    self.output.add_info('E', pkg, 'executable-docs', f)

    def _check_doc_file_dependencies(self, pkg):
        """
        Check if docfiles create additional dependencies in the package and
        print a warning if so.
        """
        files = pkg.files

        reqs = {}
        for fname, pkgfile in files.items():
            reqs[fname] = [x[0] for x in pkgfile.requires]

        core_reqs = {}  # dependencies of non-doc files
        doc_reqs = {}   # dependencies of doc files

        for dep in pkg.header.dsFromHeader():
            # skip deps which were found by find-requires
            if dep.Flags() & rpm.RPMSENSE_FIND_REQUIRES != 0:
                continue
            core_reqs[dep.N()] = []

        # register things which are provided by the package
        for i in pkg.header[rpm.RPMTAG_PROVIDES]:
            core_reqs[byte_to_string(i)] = []
        for i in files:
            core_reqs[i] = []

        for i in files:
            if not reqs[i]:
                continue  # skip empty dependencies
            if i in pkg.doc_files:
                target = doc_reqs
            else:
                target = core_reqs

            for r in reqs[i]:
                if r not in target:
                    target[r] = []
                target[r].append(i)

        # go through the calculated requirements of the %doc files
        for (dep, req_files) in doc_reqs.items():
            if dep not in core_reqs:
                for f in req_files:
                    self.output.add_info('W', pkg, 'doc-file-dependency', f, dep)

    def _check_unwanted_files(self, pkg):
        """
        Check if docfiles contain unwanted files.

        Now it checks the presence of the INSTALL file that is often not
        relevant for the built package.
        """
        for docfile in pkg.doc_files:
            if docfile.endswith('/INSTALL'):
                self.output.add_info('W', pkg, 'install-file-in-docs', docfile)

    def _check_huge_docs(self, pkg):
        """
        Check the size of the documentation in the package and print a warning
        if it's more than half of the size of the package.
        """
        files = pkg.files
        complete_size = 0
        for _, pkgfile in files.items():
            if stat.S_ISREG(pkgfile.mode):
                complete_size += pkgfile.size

        doc_size = 0
        for f in pkg.doc_files:
            if stat.S_ISREG(files[f].mode):
                doc_size += files[f].size

        if doc_size * 2 >= complete_size and doc_size > 100 * 1024:
            self.output.add_info('W', pkg, 'package-with-huge-docs: %3d%%' % (doc_size * 100 / complete_size))
