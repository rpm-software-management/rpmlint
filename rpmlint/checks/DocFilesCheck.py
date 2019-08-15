import rpm
from rpmlint.checks.AbstractCheck import AbstractCheck
from rpmlint.helpers import byte_to_string


class DocFilesCheck(AbstractCheck):
    def __check_requirements(self, pkg):

        doc_files = pkg.docFiles()
        files = pkg.files()

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
            if i in doc_files:
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

    def __check_unwanted_files(self, pkg):

        for docfile in pkg.docFiles():
            if docfile.endswith('/INSTALL'):
                self.output.add_info('W', pkg, 'install-file-in-docs', docfile)

    def check_binary(self, pkg):

        if not pkg.docFiles():
            return

        self.__check_requirements(pkg)
        self.__check_unwanted_files(pkg)
