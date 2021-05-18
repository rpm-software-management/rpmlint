import os
from re import split
from xml.dom.minidom import parse
from xml.parsers.expat import ExpatError

from rpmlint.checks.AbstractCheck import AbstractCheck


class PolkitCheck(AbstractCheck):
    """Note: This expects the package polkit-default-privs to be installed to work."""
    def __init__(self, config, output):
        super().__init__(config, output)
        self.polkit_privs_whitelist = config.configuration.get('PolkitPrivsWhitelist', ())
        self.polkit_privs_files = config.configuration.get('PolkitPrivsFiles', ['/etc/polkit-default-privs.standard'])
        self.privs = {}
        self._collect_privs()

    def _collect_privs(self):
        for filename in self.polkit_privs_files:
            if os.path.exists(filename):
                self._parse_privs_file(filename)

    def _parse_privs_file(self, filename):
        with open(filename) as inputfile:
            for line in inputfile:
                line = line.split('#')[0].rstrip()
                if line:
                    line = split(r'\s+', line)
                    priv = line[0]
                    value = line[1]
                    self.privs[priv] = value

    def check_perm_files(self, pkg):
        """Checks files in polkit-default-privs.d."""
        prefix = '/etc/polkit-default-privs.d/'
        profiles = ('restrictive', 'standard', 'relaxed')
        permfiles = []
        # first pass, find additional files
        for f in pkg.files:
            if f.startswith(prefix):
                if f in pkg.ghost_files:
                    self.output.add_info('E', pkg, 'polkit-ghost-file', f)
                    continue

                bn = f[len(prefix):]
                if bn not in self.polkit_privs_whitelist:
                    self.output.add_info('E', pkg, 'polkit-unauthorized-file', f)

                parts = bn.rsplit('.', 1)
                if len(parts) == 2 and parts[-1] in profiles:
                    bn = parts[0]

                if bn not in permfiles:
                    permfiles.append(bn)

        for f in sorted(permfiles):
            f = pkg.dirName() + prefix + f
            for profile in profiles:
                path = '.'.join((f, profile))
                if os.path.exists(path):
                    self._parse_privs_file(path)
                    break
            else:
                self._parse_privs_file(f)

    def check_actions(self, pkg):
        """Checks files in the actions directory."""
        prefix = '/usr/share/polkit-1/actions/'
        for f in pkg.files:
            # catch xml exceptions
            try:
                if f.startswith(prefix):
                    if f in pkg.ghost_files:
                        self.output.add_info('E', pkg, 'polkit-ghost-file', f)
                        continue

                    xml = parse(pkg.dirName() + f)
                    for a in xml.getElementsByTagName('action'):
                        self.check_action(pkg, a)
            except ExpatError as x:
                self.output.add_info('E', pkg, 'polkit-xml-exception', f'{f:s} raised an exception: {x}')
                continue

    def check_action(self, pkg, action):
        """Inspect a single polkit action used by an application."""
        action_id = action.getAttribute('id')
        if action_id in self.privs:
            # the action is explicitly whitelisted, nothing else to do
            return

        allow_types = ('allow_any', 'allow_inactive', 'allow_active')
        foundunauthorized = False
        foundno = False
        foundundef = False
        settings = {}
        try:
            defaults = action.getElementsByTagName('defaults')[0]
            for i in defaults.childNodes:
                if not i.nodeType == i.ELEMENT_NODE:
                    continue

                if i.nodeName in allow_types:
                    settings[i.nodeName] = i.firstChild.data
        except KeyError:
            foundunauthorized = True

        for i in allow_types:
            if i not in settings:
                foundundef = True
                settings[i] = 'no'
            elif settings[i].find('auth_admin') != 0:
                if settings[i] == 'no':
                    foundno = True
                else:
                    foundunauthorized = True

        action_settings = f'{action_id} ({settings[allow_types[0]]}:{settings[allow_types[1]]}:{settings[allow_types[2]]})'
        if foundunauthorized:
            self.output.add_info('E', pkg, 'polkit-unauthorized-privilege', action_settings)
        else:
            self.output.add_info('E', pkg, 'polkit-untracked-privilege', action_settings)
        if foundno or foundundef:
            self.output.add_info('I', pkg, 'polkit-cant-acquire-privilege', action_settings)

    def check(self, pkg):
        if pkg.is_source:
            return

        self.check_perm_files(pkg)
        self.check_actions(pkg)
