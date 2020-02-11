from os.path import basename
import stat

import rpm
from rpmlint.checks.AbstractCheck import AbstractCheck
from rpmlint.pkg import b2s


class UpdateAlternativesCheck(AbstractCheck):
    """
    Check for compliance with SUSE's update-alternatives guidelines:
      http://en.opensuse.org/openSUSE:Packaging_Multiple_Version_guidelines
    """

    INSTALL = '--install'

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
                if not arg.startswith('--'):
                    command_args.append(arg)

            ghost_files.add(command_args[0])

            SLAVE = '--slave'

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
            alt_files.update(self.read_ghost_files(b2s(script)))

        files = pkg.files()
        ghost_files = pkg.ghostFiles()

        for af in alt_files:
            # /etc/alternatives/$(basename) should be a ghost file
            etc_alt_file = '/etc/alternatives/%s' % basename(af)

            if etc_alt_file not in files:
                self.output.add_info('E', pkg, 'alternative-link-missing', etc_alt_file)
            elif etc_alt_file not in ghost_files:
                self.output.add_info('E', pkg, 'alternative-link-not-ghost', etc_alt_file)

            # generic-name should be a symlink to /etc/alternatives/$(basename)
            if af not in files:
                self.output.add_info('E', pkg, 'alternative-generic-name-missing', af)
            elif not stat.S_ISLNK(files[af].mode):
                self.output.add_info('E', pkg, 'alternative-generic-name-not-symlink', af)
