import os
from re import split
from xml.dom.minidom import parse
from xml.parsers.expat import ExpatError

from rpmlint.checks.AbstractCheck import AbstractCheck


class PolkitCheck(AbstractCheck):
    """ Enforces whitelistings for polkit policies.

    Note: This expects the package `polkit-default-privs` to be installed to work.

    This check enforces a whitelisting for polkit policies installed by packages. openSUSE uses the package
    `polkit-default-privs` to apply one of a selection of default system profiles for polkit actions. A package's polkit
    action is considered whitelisted if an entry for it is existing in polkit-default-priv's standard profile.

    Apart from this this check also performs minor consistency checks and gives suggestions to packages regarding
    installed polkit policies.
    """
    def __init__(self, config, output):
        super().__init__(config, output)
        self.polkit_privs_files = config.configuration.get('PolkitPrivsFiles', ['/usr/etc/polkit-default-privs/profiles/standard'])
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
        found_unauthorized = False
        settings = {}
        try:
            defaults = action.getElementsByTagName('defaults')[0]
            for i in defaults.childNodes:
                if not i.nodeType == i.ELEMENT_NODE:
                    continue

                if i.nodeName in allow_types:
                    settings[i.nodeName] = i.firstChild.data
        except KeyError:
            found_unauthorized = True

        for i in allow_types:
            if i not in settings:
                # If the authorization setting is left out for a certain category in the XML
                # policy then the default applied by polkit is `no` This is not really
                # documented in the polkit man page but can be learned from the polkit source
                # code where the `ParserData` is zero initialized and a zero implicit corresponds
                # to `no`.
                settings[i] = 'no'
            elif settings[i].find('auth_admin') != 0:
                if settings[i] != 'no':
                    found_unauthorized = True

        action_settings = f'{action_id} ({settings[allow_types[0]]}:{settings[allow_types[1]]}:{settings[allow_types[2]]})'
        if found_unauthorized:
            self.output.add_info('W', pkg, 'polkit-user-privilege', action_settings)
        else:
            self.output.add_info('E', pkg, 'polkit-untracked-privilege', action_settings)

    def check(self, pkg):
        if pkg.is_source:
            return

        self.check_actions(pkg)
