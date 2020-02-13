from xml.dom.minidom import parse

from rpmlint.checks.AbstractCheck import AbstractCheck


class DBusPolicyCheck(AbstractCheck):
    def check(self, pkg):
        if pkg.is_source:
            return

        for f in pkg.files:
            if f in pkg.ghost_files:
                continue

            # catch xml exceptions
            try:
                if f.startswith('/etc/dbus-1/system.d/'):
                    send_policy_seen = False
                    lf = pkg.dirName() + f
                    xml = parse(lf)
                    for policy in xml.getElementsByTagName('policy'):
                        send_policy_seen = self._check_allow_policy_element(pkg, f, policy) or send_policy_seen
                        self._check_deny_policy_element(pkg, f, policy)

                    if not send_policy_seen:
                        self.output.add_info('E', pkg, 'communication not allowed', f)

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

        return send_policy_seen

    def _check_deny_policy_element(self, pkg, f, policy):
        for deny in policy.getElementsByTagName('deny'):
            if (deny.hasAttribute('send_interface') and not
                    deny.hasAttribute('send_destination')):
                self.output.add_info('E', pkg, 'dbus-policy-deny-without-destination', deny.toxml(), f)
