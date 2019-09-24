from pathlib import Path
import stat

from rpmlint.checks.AbstractCheck import AbstractCheck


class RCLinksCheck(AbstractCheck):
    def check(self, pkg):
        if pkg.isSource():
            return

        rclinks = set()
        rccandidates = set()
        initscripts = set()

        for fname, pkgfile in pkg.files().items():
            if fname in pkg.ghostFiles():
                continue

            if (stat.S_ISLNK(pkgfile.mode) and
                    (fname.startswith('/usr/sbin/rc') or
                     fname.startswith('/sbin/rc'))):
                rclinks.add(fname.partition('/rc')[2])
            elif fname.startswith('/usr/lib/systemd/system/'):
                basename = Path(fname).name
                if '@' in fname:
                    continue
                if fname.endswith('.service') or fname.endswith('.target'):
                    rccandidates.add(basename.rpartition('.')[0])
            elif fname.startswith('/etc/init.d/'):
                basename = Path(fname).name
                if not (basename.startswith('rc') or
                        basename.startswith('boot.')):
                    initscripts.add(basename)

        for fname in sorted(initscripts):
            if fname in rccandidates:
                self.output.add_info('E', pkg, 'systemd-shadowed-initscript', fname)
            else:
                rccandidates.add(fname)

        for fname in sorted(rccandidates):
            if fname not in sorted(rclinks):
                self.output.add_info('W', pkg, 'missing-rclink', fname)
