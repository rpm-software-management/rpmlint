from pathlib import Path
import stat

from rpmlint.checks.AbstractCheck import AbstractCheck


class DocCheck(AbstractCheck):
    """
    Checks for package documentation.
    """

    def check(self, pkg):
        if pkg.isSource():
            return

        self._check_executable_docs(pkg)
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
        files = pkg.files()
        for f in pkg.docFiles():
            mode = files[f].mode
            if not stat.S_ISREG(mode) or not mode & 0o111:
                continue
            path = Path(f)
            extensions = ['.txt', '.gif', '.jpg', '.html', '.pdf', '.ps', '.pdf.gz', '.ps.gz']
            if path.suffix in extensions:
                self.output.add_info('E', pkg, 'executable-docs', f)

            for name in ['README', 'NEWS', 'COPYING', 'AUTHORS', 'LICENCE', 'LICENSE']:
                if path.name.lower() == name.lower():
                    self.output.add_info('E', pkg, 'executable-docs', f)

    def _check_huge_docs(self, pkg):
        """
        Check the size of the documentation in the package and print a warning
        if it's more than half of the size of the package.
        """
        files = pkg.files()
        complete_size = 0
        for _, pkgfile in files.items():
            if stat.S_ISREG(pkgfile.mode):
                complete_size += pkgfile.size

        doc_size = 0
        for f in pkg.docFiles():
            if stat.S_ISREG(files[f].mode):
                doc_size += files[f].size

        if doc_size * 2 >= complete_size and doc_size > 100 * 1024:
            self.output.add_info('W', pkg, 'package-with-huge-docs: %3d%%' % (doc_size * 100 / complete_size))
