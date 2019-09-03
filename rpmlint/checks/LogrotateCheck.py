# vim:sw=4:et
#############################################################################
# File          : CheckLogrotate.py
# Package       : rpmlint
# Author        : Ludwig Nussel
# Purpose       : Check for insecure logrotate directories
#############################################################################

from Filter import printError, addDetails
import AbstractCheck
import os


class LogrotateCheck(AbstractCheck.AbstractCheck):
    def __init__(self):
        AbstractCheck.AbstractCheck.__init__(self, "CheckLogrotate")

    def check(self, pkg):
        if pkg.isSource():
            return

        files = pkg.files()
        dirs = {}

        for f in files:
            if f in pkg.ghostFiles():
                continue

            if f.startswith("/etc/logrotate.d/"):
                try:
                    for n, o in self.parselogrotateconf(pkg.dirName(), f).items():
                        if n in dirs and dirs[n] != o:
                            printError(pkg, "logrotate-duplicate", n)
                        else:
                            dirs[n] = o
                except Exception as x:
                    printError(pkg, 'rpmlint-exception', "%(file)s raised an exception: %(x)s" % {'file': f, 'x': x})

        for d in sorted(dirs.keys()):
            if d not in files:
                if d != '/var/log':
                    printError(pkg, 'suse-logrotate-log-dir-not-packaged', d)
                continue
            mode = files[d].mode & 0o777
            if files[d].user != 'root' and (dirs[d] is None or dirs[d][0] != files[d].user):
                printError(
                    pkg, 'suse-logrotate-user-writable-log-dir',
                    "%s %s:%s %04o" % (d, files[d].user, files[d].group, mode))
            elif files[d].group != 'root' and mode & 0o20 and (dirs[d] is None or dirs[d][1] != files[d].group):
                printError(
                    pkg, 'suse-logrotate-user-writable-log-dir',
                    "%s %s:%s %04o" % (d, files[d].user, files[d].group, mode))

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
                            if len(logfile) == 0 or logfile == '{':
                                continue
                            dn = os.path.dirname(logfile)
                            if dn not in dirs:
                                currentdirs.append(dn)
                                dirs[dn] = None
                else:
                    if line.endswith('}'):
                        currentdirs = []
                    elif line.startswith("su "):
                        a = line.split(" ")
                        for dn in currentdirs:
                            dirs[dn] = (a[1], a[2])
        return dirs


check = LogrotateCheck()

addDetails(
'suse-logrotate-duplicate',
"""There are dupliated logrotate entries with different settings for
the specified file""",

'suse-logrotate-user-writable-log-dir',
"""The log directory is writable by unprivileged users. Please fix
the permissions so only root can write there or add the 'su' option
to your logrotate config""",

'suse-logrotate-log-dir-not-packaged',
"""Please add the specified directory to the file list to be able to
check permissions"""
)
