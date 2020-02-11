# vim:sw=4:et
# File          : CheckUpdateAlternatives
# Package       : rpmlint
# Author        : SUSE Linux Products GmbH
# Purpose       : Check if update-alternatives is used properly

from Filter import printWarning, addDetails, Config

import AbstractCheck
import os
import rpm
import stat
import Pkg


class CheckUpdateAlternatives(AbstractCheck.AbstractCheck):

    """Check for compliance with SUSE's update-alternatives guidelines.

    See
    http://en.opensuse.org/openSUSE:Packaging_Multiple_Version_guidelines

    """

    INSTALL = "--install"

    def __init__(self):
        AbstractCheck.AbstractCheck.__init__(self, "CheckUpdateAlternatives")

    @classmethod
    def read_ghost_files(cls, script):

        if not script or 'update-alternatives' not in script:
            return set()

        ghost_files = set()

        for command in (
                c.replace('\\\n', '').replace('"', '').strip()
                for c in script.split('update-alternatives')
                if cls.INSTALL in c):

            # parse install
            command_args = []
            for arg in command.split(None):
                if not arg.startswith("--"):
                    command_args.append(arg)

            ghost_files.add(command_args[0])

            SLAVE = "--slave"

            if SLAVE in command:
                for sc in (
                        c.strip()
                        for c in command[command.index(SLAVE):].split(SLAVE)
                        if c.strip() != ''):

                    xs = sc.split(None, 2)
                    ghost_files.add(xs[0])

        return ghost_files

    def check(self, pkg):

        if pkg.isSource():
            return

        alt_files = set()
        for script in (pkg.header[tag]
                       for tag in (rpm.RPMTAG_POSTIN,
                                   rpm.RPMTAG_PREIN,
                                   rpm.RPMTAG_POSTTRANS)):
            alt_files.update(self.read_ghost_files(Pkg.b2s(script)))

        files = pkg.files()
        ghost_files = pkg.ghostFiles()

        for af in alt_files:
            # /etc/alternatives/$(basename) should be a ghost file
            etc_alt_file = "/etc/alternatives/%s" % os.path.basename(af)

            if etc_alt_file not in files:
                printWarning(pkg,
                             'suse-alternative-link-missing', etc_alt_file)
            elif etc_alt_file not in ghost_files:
                printWarning(pkg,
                             'suse-alternative-link-not-ghost', etc_alt_file)

            # generic-name should be a symlink to /etc/alternatives/$(basename)
            if af not in files:
                printWarning(pkg,
                             'suse-alternative-generic-name-missing', af)
            elif not stat.S_ISLNK(files[af].mode):
                printWarning(pkg,
                             'suse-alternative-generic-name-not-symlink', af)

            # TODO check that %post contains --install call
            # TODO check that %preun contains --remove call


check = CheckUpdateAlternatives()

if Config.info:
    addDetails(
'suse-alternative-generic-name-not-symlink',
'''The update-alternative generic-name is not a symlink pointing to
%{_sysconfdir}/alternatives/$(basename generic-name).
''',

'suse-alternative-link-not-ghost',
'''The %{_sysconfdir}/alternatives/$(basename generic-name) link exists but is
not marked as ghost. Mark it as %ghost.''',

'suse-alternative-link-missing',
'''The file %{_sysconfdir}/alternatives/$(basename generic-name) is missing
in the file list. Mark it as %ghost and add it to the file list.''',

'suse-alternative-generic-name-missing',
'''The update-alternatives generic name is not in the filelist. Create it as
a symlink to %{_sysconfdir}/alternatives/$(basename generic-name) and add it
to the file list.''')
