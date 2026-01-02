from xml.dom.minidom import parse

from rpmlint.checks.AbstractCheck import AbstractCheck

DBUS_DIRECTORIES = ('/etc/dbus-1/system.d/', '/usr/share/dbus-1/system.d/')


class DBusPolicyCheck(AbstractCheck):
    def check(self, pkg):
        if pkg.is_source:
            return

        for f in pkg.files:
            if f in pkg.ghost_files:
                continue

            # catch xml exceptions
            try:
                if any(f.startswith(d) for d in DBUS_DIRECTORIES):
                    send_policy_seen = False
                    lf = pkg.dir_name() + f
                    xml = parse(lf)
                    for policy in xml.getElementsByTagName('policy'):
                        send_policy_seen |= self._check_allow_policy_element(pkg, f, policy)
                        self._check_deny_policy_element(pkg, f, policy)

                    if not send_policy_seen:
                        self.output.add_info('E', pkg, 'dbus-policy-missing-allow', f)

            except Exception as e:
                self.output.add_info('E', pkg, 'dbus-parsing-exception', 'raised an exception: ' + str(e), f)
                continue

    def _check_allow_policy_element(self, pkg, f, policy):
        send_policy_seen = False
        for allow in policy.getElementsByTagName('allow'):
            if ((allow.hasAttribute('send_interface') or
                 allow.hasAttribute('send_member') or
                 allow.hasAttribute('send_path')) and not
                    allow.hasAttribute('send_destination')):
                send_policy_seen = True
                self.output.add_info('E', pkg, 'dbus-policy-allow-without-destination', allow.toxml(), f)
            elif allow.hasAttribute('send_destination'):
                send_policy_seen = True

            if (allow.hasAttribute('receive_sender') or
                    allow.hasAttribute('receive_interface')):
                self.output.add_info('W', pkg, 'dbus-policy-allow-receive', allow.toxml(), f)

            # to prevent bugs like bsc#1220215, scan for any attributes like
            # send_destination="*" and reject them

            for key, val in allow.attributes.items():
                # Ignore member settings, these can have valid use cases for
                # wildcards.
                if key == 'send_member':
                    continue

                # Otherwise inspect all attributes starting with 'send_',
                # there's quite a lot of them and most support an asterisk as
                # value.
                #
                # In theory there could be valid use cases when this is not in
                # context="default" but restricted to some specific, powerful
                # user account or group, but at the moment no such example is
                # known.
                #
                # According to documentation only a single "*" may appear or a
                # fixed string, nothing like "org.*". We are still checking
                # for appearance of any wildcard in the string; there should
                # not be any valid use cases for an asterisk appearing there
                # and this way we might catch some additional cases of weird
                # things going on.
                if key.startswith('send_') and '*' in val:
                    self.output.add_info('E', pkg, 'dbus-policy-allow-wildcard', allow.toxml(), f)

        return send_policy_seen

    def _check_deny_policy_element(self, pkg, f, policy):
        for deny in policy.getElementsByTagName('deny'):
            if (deny.hasAttribute('send_interface') and not
                    deny.hasAttribute('send_destination')):
                self.output.add_info('E', pkg, 'dbus-policy-deny-without-destination', deny.toxml(), f)
