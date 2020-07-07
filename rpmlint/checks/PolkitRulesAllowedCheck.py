from rpmlint.checks.Allowlisting import AbstractAllowlistCheck


class PolkitRulesAllowedCheck(AbstractAllowlistCheck):
    """ Checks that polkit rules files are on an allow list. """

    restricted_paths = (
        '/etc/polkit-1/rules.d/',
        '/usr/share/polkit-1/rules.d/',
    )
    error_map = {
        'unauthorized': 'polkit-unauthorized-rules',
        'changed': 'polkit-changed-rules',
        'ghost': 'polkit-ghost-file',
    }

    @property
    def allowlist_filenames(self):
        return self.config.configuration.get('PolkitRulesWhitelist', ())
