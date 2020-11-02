from os.path import basename
import re
import stat

import rpm
from rpmlint.checks.AbstractCheck import AbstractCheck
from rpmlint.helpers import byte_to_string


class AlternativesCheck(AbstractCheck):
    """
    Check for compliance with update-alternatives usage guidelines:
      http://en.opensuse.org/openSUSE:Packaging_Multiple_Version_guidelines
      https://docs.fedoraproject.org/en-US/packaging-guidelines/Alternatives/
    In short the rules are:
      /etc/alternative/basename must be in %files and must be %ghost file
      The alternative master must be a symlink to /etc and in filelist. I.e.:
        /usr/bin/basename -> /etc/alternative/basename
      In %post the update-alternatives with install must be called
      In %postun the update-alternatives with remove must be called
      Requires(post) and Requires(postun) must depend on update-alternatives
    """
    # Regex to match anything that can be in requires for update-alternatives
    re_requirement = re.compile(r'^(/usr/sbin/|%{?_sbindir}?/)?update-alternatives$')
    re_install = re.compile(r'--install\s+(?P<link>\S+)\s+(?P<name>\S+)\s+(\S+)\s+(\S+)')
    re_slave = re.compile(r'--slave\s+(?P<link>\S+)\s+(\S+)\s+(\S+)')
    command = 'update-alternatives'

    def __init__(self, config, output):
        super().__init__(config, output)
        # Containers for scriptlets as they will be used on multiple places
        self.post = None
        self.postun = None
        self.install_binaries = {}
        self.slave_binaries = []

    def check(self, pkg):
        if pkg.is_source:
            return

        # populate scriptlets
        self.post = byte_to_string(pkg.header[rpm.RPMTAG_POSTIN])
        self.postun = byte_to_string(pkg.header[rpm.RPMTAG_POSTUN])

        if not self._check_ua_presence(pkg):
            return

        self._check_requirements(pkg)
        self._check_post_phase(pkg, self.post)
        self._check_postun_phase(pkg, self.postun)
        self._check_filelist(pkg)

    def _find_u_a_binarires(self, line):
        """
        Find all binaries that have install or slave that are needed
        to be validated.
        update-alternatives --install link name path priority [--slave link name path]+
        """
        match = self.re_install.search(line)
        if match:
            self.install_binaries[match.group('link')] = match.group('name')
        # --slave can be repeated multiple times
        matches = self.re_slave.finditer(line)
        for match in matches:
            self.slave_binaries.append(match.group('link'))

    def _check_post_phase(self, pkg, script):
        """
        Validate that post phase contains the update-alternatives --install call
        Collect all binaries that are to be validated for the usage
        """
        script = self._normalize_script(script)
        # If there is no u-a call then give up right away
        if not script:
            self.output.add_info('E', pkg, 'update-alternatives-post-call-missing')
            return
        # collect all the known binaries
        for line in script:
            self._find_u_a_binarires(line)
        # if there is u-a call, but no --install command it is still an issue
        if not self.install_binaries:
            self.output.add_info('E', pkg, 'update-alternatives-post-call-missing')

    def _check_postun_phase(self, pkg, script):
        """
        Validate that post phase contains the update-alternatives --remove call
        Make sure there is --remove line for all installed binaries
        update-alternatives --remove name path
        """
        script = self._normalize_script(script)
        # If there is no u-a call then give up right away
        if not script:
            self.output.add_info('E', pkg, 'update-alternatives-postun-call-missing')
            return
        # validate each binary actually is properly removed
        binaries = list(self.install_binaries.values())
        for binary in binaries:
            re_remove = re.compile(r'--remove\s+{}\b'.format(binary))
            for line in script:
                if re_remove.search(line) and binary in binaries:
                    binaries.remove(binary)
        for binary in binaries:
            self.output.add_info('E', pkg, 'update-alternatives-postun-call-missing', binary)

    def _check_filelist(self, pkg):
        """
        Validate all filelists for required content to make u-a work:
        * For each install/slave binary I need /etc/alternatives/X
          + This file must be in filelist marked as ghost
        * The install/slave binary must be present in filelist
          + The item must be a a link to /etc/alternatives
        """
        files = pkg.files
        ghost_files = pkg.ghost_files
        for binary in self.slave_binaries + list(self.install_binaries.keys()):
            etc_alt_file = '/etc/alternatives/%s' % basename(binary)
            if etc_alt_file not in files:
                # The alternative is missing completely
                self.output.add_info('E', pkg, 'alternative-link-missing', etc_alt_file)
            elif etc_alt_file not in ghost_files:
                # The alternative is present, but not as ghost
                self.output.add_info('E', pkg, 'alternative-link-not-ghost', etc_alt_file)

            # generic-name should be a symlink to /etc/alternatives/$(basename)
            if binary not in files:
                self.output.add_info('E', pkg, 'alternative-generic-name-missing', binary)
            elif not stat.S_ISLNK(files[binary].mode):
                self.output.add_info('E', pkg, 'alternative-generic-name-not-symlink', binary)

    def _check_ua_presence(self, pkg):
        """
        Check if there is update-alternatives scriptlet present and if we should do validation
        """
        # first check just if we have anything in /etc/alternatives
        for path in pkg.files:
            if path.startswith('/etc/alternatives'):
                return True
        # then check the scriptlets if they run update-alternatives
        if self._check_scriptlet_for_alternatives(self.post):
            return True
        if self._check_scriptlet_for_alternatives(self.postun):
            return True
        return False

    def _check_scriptlet_for_alternatives(self, scriptlet):
        """
        Check if scriptlet actually contains the update-alternatives call
        """
        if scriptlet is not None and self.command in scriptlet:
            return True
        return False

    def _normalize_script(self, script):
        """
        Remove "backslash+newline" to keep all commands as oneliners.
        Remove single and double quotes everywhere.
        Keep only the line that contains the update-alternatives call.
        Return the list of lines that contain update-alternatives calls
        """
        # with old rpm we get wrong type
        script = byte_to_string(script)
        if script is None:
            return None
        script = script.replace('\\\n', '')
        script = script.replace('"', '')
        script = script.replace("'", '')
        script = script.strip()
        return [i for i in script.splitlines() if self.command in i]

    def _check_requirements(self, pkg):
        """
        Check that Requires(post/postun) contain the update-alternatives dependency
        """
        for require in pkg.prereq:
            if self.re_requirement.match(require[0]):
                return
        self.output.add_info('E', pkg, 'update-alternatives-requirement-missing')
