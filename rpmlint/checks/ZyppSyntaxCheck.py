from rpmlint.checks.AbstractCheck import AbstractCheck


class ZyppSyntaxCheck(AbstractCheck):
    def check(self, pkg):
        # We care only about the names, versions are pointless here
        pkg_supplements = [x.name for x in pkg.supplements]
        pkg_enhances = [x.name for x in pkg.enhances]
        pkg_recommends = [x.name for x in pkg.recommends]
        pkg_suggests = [x.name for x in pkg.suggests]
        pkg_requires = [x.name for x in pkg.requires]
        pkg_conflicts = [x.name for x in pkg.conflicts]
        keywords = pkg_supplements + pkg_enhances + pkg_recommends + pkg_suggests + pkg_requires + pkg_conflicts
        for keyword in keywords:
            if keyword.startswith('packageand('):
                self.output.add_info('E', pkg, 'suse-zypp-packageand', keyword)
            if keyword.startswith('otherproviders('):
                self.output.add_info('E', pkg, 'suse-zypp-otherproviders', keyword)
