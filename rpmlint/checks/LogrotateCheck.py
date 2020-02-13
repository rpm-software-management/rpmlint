import os

from rpmlint.checks.AbstractCheck import AbstractCheck


class LogrotateCheck(AbstractCheck):
    def check(self, pkg):
        if pkg.is_source:
            return

        files = pkg.files
        dirs = {}

        for f in files:
            if f in pkg.ghost_files:
                continue

            if f.startswith('/etc/logrotate.d/'):
                try:
                    for n, o in self.parselogrotateconf(pkg.dirName(), f).items():
                        if n in dirs and dirs[n] != o:
                            self.output.add_info('E', pkg, 'logrotate-duplicate', n)
                        else:
                            dirs[n] = o
                except Exception as e:
                    self.output.add_info('E', pkg, 'logrotate-exception', f, str(e))

        for d in sorted(dirs.keys()):
            if d not in files:
                self.output.add_info('E', pkg, 'logrotate-log-dir-not-packaged', d)
                continue
            mode = files[d].mode & 0o777
            if files[d].user != 'root' and (dirs[d] is None or dirs[d][0] != files[d].user):
                self.output.add_info('E', pkg, 'logrotate-user-writable-log-dir',
                                     '%s %s:%s %04o' % (d, files[d].user, files[d].group, mode))
            elif files[d].group != 'root' and mode & 0o20 and (dirs[d] is None or dirs[d][1] != files[d].group):
                self.output.add_info('E', pkg, 'logrotate-user-writable-log-dir',
                                     '%s %s:%s %04o' % (d, files[d].user, files[d].group, mode))

    # extremely primitive logrotate parser
    def parselogrotateconf(self, root, f):
        dirs = {}
        with open('/'.join((root, f))) as fd:
            currentdirs = []
            for line in fd.readlines():
                line = line.strip()
                if line.startswith('#'):
                    continue
                if not currentdirs:
                    if line.endswith('{'):
                        for logfile in line.split(' '):
                            logfile = logfile.strip()
                            if not logfile or logfile == '{':
                                continue
                            dn = os.path.dirname(logfile)
                            if dn not in dirs:
                                currentdirs.append(dn)
                                dirs[dn] = None
                else:
                    if line.endswith('}'):
                        currentdirs = []
                    elif line.startswith('su '):
                        a = line.split(' ')
                        for dn in currentdirs:
                            dirs[dn] = (a[1], a[2])
        return dirs
