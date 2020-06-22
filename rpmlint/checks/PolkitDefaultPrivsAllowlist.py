""" Lints to enforce that polkit rules and actions are allowed in the
(open)SUSE specific 'polkit-default-privs' mechanism. """

from xml.dom.minidom import parse

from .AbstractCheck import AbstractFilesCheck
from .Allowlisting import AbstractSimpleAllowlistCheck


POLKIT_DEFAULT_PRIVS_D = '/etc/polkit-default-privs.d/'


class PolkitDefaultPrivsOverrideCheck(AbstractSimpleAllowlistCheck):
    """ Checks that files that override polkit-default-privs configuration are on an allow list. """
    restricted_paths = (POLKIT_DEFAULT_PRIVS_D,)
    error_map = {
        'unauthorized': 'polkit-unauthorized-file',
        'ghost': 'polkit-ghost-file'
    }
    allowlist_config_key = 'PolkitRulesWhitelist'


class PolkitActionsCheck(AbstractFilesCheck):
    """ Checks that polkit actions are allowed through polkit-default-privs. """
    def __init__(self, config, output):
        super().__init__(config, output, r'^/usr/share/polkit-1/actions/')
        self._privs = None

    def check_binary(self, pkg):
        self._collect_privs(pkg)

        # `check_file` is not called for ghost files, so handle them here separately
        for f in pkg.ghost_files:
            if f.startswith('/usr/share/polkit-1/actions/'):
                self.output.add_info('E', pkg, 'polkit-ghost-file', f)

        super().check_binary(pkg)

    def check_file(self, pkg, filename):
        """Checks files in the actions directory."""
        f = pkg.files[filename]

        try:
            # minidom is secure against XML retrieval attacks, but malicious XML
            # can cause unbounded memory or CPU usage - which we can live with
            xml = parse(f.path)
        except Exception as x:
            self.output.add_info('E', pkg, 'rpmlint-exception', f'{filename} raised an exception: {x}')
            return
        for a in xml.getElementsByTagName('action'):
            self._check_action(pkg, a)

    def _collect_privs(self, pkg):
        self._privs = {}
        for filename in self.config.configuration.get('PolkitPrivsFiles', ('/etc/polkit-default-privs.standard',)):
            try:
                self._parse_privs_file(filename)
            except FileNotFoundError:
                pass

        permfiles = []
        profiles = ('restrictive', 'standard', 'relaxed')
        # first pass: find additional files
        for path, f in pkg.files.items():
            if path.startswith(POLKIT_DEFAULT_PRIVS_D) and not f.is_ghost:
                bn = path[len(POLKIT_DEFAULT_PRIVS_D):]
                parts = bn.rsplit('.', 1)

                if len(parts) == 2 and parts[1] in profiles:
                    bn = parts[0]

                if bn not in permfiles:
                    permfiles.append(bn)

        # second pass: parse these files
        for f in sorted(permfiles):
            f = pkg.dirName() + POLKIT_DEFAULT_PRIVS_D + f

            # prefer parsing profile-specific files (in most-to-least restrictive order)
            for profile in profiles:
                try:
                    self._parse_privs_file(f'{f}.{profile}')
                    break
                except FileNotFoundError:
                    pass
            else:
                # fall-back to generic file if no profile-specific one was found
                self._parse_privs_file(f)

    def _parse_privs_file(self, filename):
        with open(filename) as inputfile:
            for line in inputfile:
                line = line.split('#')[0].rstrip('\n')
                if line:
                    priv, value, *_ = line.split()
                    self._privs[priv] = value

    def _check_action(self, pkg, action):
        """Inspect a single polkit action used by an application."""
        action_id = action.getAttribute('id')

        if action_id in self._privs:
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
                settings[i] = '??'
            elif settings[i].find('auth_admin') != 0:
                if settings[i] == 'no':
                    foundno = True
                else:
                    foundunauthorized = True

        action_settings = '{} ({}:{}:{})'.format(action_id, *(settings[t] for t in allow_types))

        if foundunauthorized:
            self.output.add_info('E', pkg, 'polkit-unauthorized-privilege', action_settings)
        else:
            self.output.add_info('E', pkg, 'polkit-untracked-privilege', action_settings)

        if foundno or foundundef:
            self.output.add_info('E', pkg, 'polkit-cant-acquire-privilege', action_settings)
