from os.path import basename
from pathlib import Path
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
    alts_requirement = 'alts'

    def __init__(self, config, output):
        super().__init__(config, output)

    def check(self, pkg):
        if pkg.is_source:
            return

        if self._check_libalternatives_presence(pkg):
            self.output.add_info('I', pkg, 'package supports libalternatives')
            self._check_libalternatives_requirements(pkg)
            self._check_libalternatives_filelist(pkg)

        self.install_binaries = {}
        self.slave_binaries = []
        # populate scriptlets
        self.post = byte_to_string(pkg.header[rpm.RPMTAG_POSTIN])
        self.postun = byte_to_string(pkg.header[rpm.RPMTAG_POSTUN])

        if not self._check_ua_presence(pkg):
            return
        self.output.add_info('I', pkg, 'package supports update-alternatives')

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
        # we remove from the binaries list in the loop, copy it
        for binary in binaries.copy():
            re_remove = re.compile(r'--remove\s+{}\b'.format(re.escape(binary)))
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

    def _check_libalternatives_presence(self, pkg):
        """
        Check if there is libalternatives scriptlet present
        """
        # first check just if we have anything in /usr/share/libalternatives/
        for path in pkg.files:
            if path.startswith('/usr/share/libalternatives/'):
                return True
        # then check if package with the name "alts" is required
        return any(req[0] == self.alts_requirement for req in pkg.requires + pkg.prereq)

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

    def _check_libalternatives_requirements(self, pkg):
        """
        Check the requirement of package "alts"
        """
        for req in pkg.requires + pkg.prereq:
            if req[0] == self.alts_requirement:
                return
        self.output.add_info('E', pkg, 'alts-requirement-missed')

    def _check_libalternatives_filelist(self, pkg):
        """
        Checking if all links to "alts" have corresponding entries in
        /usr/share/libalternatives.
        """
        for f, pkgfile in pkg.files.items():
            if pkgfile.linkto == Path(self.alts_requirement).name:
                dir_name = '/usr/share/libalternatives/' + Path(f).name
                if dir_name not in pkg.files:
                    self.output.add_info('E', pkg, 'libalternatives-directory-not-exists', dir_name)
                else:
                    r = re.compile('^' + dir_name + '/.*.conf$')
                    if not list(filter(r.match, pkg.files)):
                        self.output.add_info('E', pkg, 'empty-libalternatives-directory', dir_name)
        """
        Checking content of all /usr/share/libalternatives/*/*.conf files
        """
        for f, pkgfile in pkg.files.items():
            if re.search('^/usr/share/libalternatives/.*conf$', f):
                filename = Path(pkg.dirname + f)
                if not filename.exists():
                    if pkgfile.is_ghost:
                        self.output.add_info('I', pkg, 'libalternatives-conf-not-found', f)
                    else:
                        self.output.add_info('E', pkg, 'libalternatives-conf-not-found', f)
                    continue
                bin_found = False
                man_found = False
                with open(filename) as read_obj:
                    # Read all lines in the file one by one. E.g:
                    #
                    # binary=/usr/bin/jupyter-3.8
                    # man=jupyter-3.8.1
                    # group=jupyter, jupyter-migrate, jupyter-troubleshoot
                    #
                    for line_nr, line in enumerate(read_obj):
                        line_array = [x.strip() for x in line.split('=')]
                        line_nr_str = f'Line: {line_nr}'
                        if len(line_array) != 2:   # empty values are valid
                            self.output.add_info('E', pkg, 'wrong-entry-format', f, line_nr_str)

                        key, value = line_array
                        if key == 'binary':
                            if bin_found:
                                self.output.add_info('E', pkg, 'multiple-entries', f, line_nr_str)
                                continue
                            for path in pkg.files:
                                if 'bin/' in path and path.endswith(value):
                                    bin_found = True
                            if not bin_found:
                                self.output.add_info('W', pkg, 'binary-entry-value-not-found', f, line_nr_str)
                        elif key == 'man':
                            if man_found:
                                self.output.add_info('E', pkg, 'double-entries', f, line_nr_str)
                                continue
                            mans = value.split(',')
                            for man in mans:
                                man_found = False
                                for path in pkg.files:
                                    if path.startswith('/usr/share/man/') and man.strip() in path:
                                        man_found = True
                                if not man_found:
                                    self.output.add_info('W', pkg, 'man-entry-value-not-found', f, line_nr_str)
                        elif key != 'group' and key != 'options':
                            self.output.add_info('W', pkg, 'wrong-tag-found', f, line_nr_str)
                    if not bin_found:
                        self.output.add_info('W', pkg, 'wrong-or-missed-binary-entry', f)
