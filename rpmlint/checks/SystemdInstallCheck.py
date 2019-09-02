from pathlib import Path
import re

import rpm
from rpmlint.checks.AbstractCheck import AbstractCheck


class SystemdInstallCheck(AbstractCheck):
    systemd_service_directory = rpm.expandMacro('%{_unitdir}')
    checked_units = ['service', 'socket', 'target', 'path']
    checked_units_regexp = re.compile('^' + systemd_service_directory + r'.+[^@]\.(' + '|'.join(checked_units) + ')$')

    def check(self, pkg):
        # Check only binary package
        if pkg.is_source:
            return

        pre = pkg[rpm.RPMTAG_PREIN] or pkg.scriptprog(rpm.RPMTAG_PREINPROG)
        post = pkg[rpm.RPMTAG_POSTIN] or pkg.scriptprog(rpm.RPMTAG_POSTINPROG)

        preun = pkg[rpm.RPMTAG_PREUN] or pkg.scriptprog(rpm.RPMTAG_PREUNPROG)
        postun = pkg[rpm.RPMTAG_POSTUN] or pkg.scriptprog(rpm.RPMTAG_POSTUNPROG)

        for fname in pkg.files:

            if self.checked_units_regexp.search(fname):
                processed = {'pre': False, 'post': False, 'preun': False, 'postun': False}

                escaped_basename = re.escape(Path(fname).name)
                PRE_POST_PATTERN = re.compile(r'for service in .*' + escaped_basename)
                PREUN_PATTERN = re.compile(r'systemctl --no-reload disable .*' + escaped_basename)
                POSTUN_PATTERN = re.compile(r'(systemctl try-restart .*|# Restart of .*)' + escaped_basename)

                for line in pre.split('\n'):
                    if PRE_POST_PATTERN.search(line):
                        processed['pre'] = True
                        break
                for line in post.split('\n'):
                    if PRE_POST_PATTERN.search(line):
                        processed['post'] = True
                        break
                for line in preun.split('\n'):
                    if PREUN_PATTERN.search(line):
                        processed['preun'] = True
                        break
                for line in postun.split('\n'):
                    if POSTUN_PATTERN.search(line):
                        processed['postun'] = True
                        break

                basename = Path(fname).name
                if not processed['pre']:
                    self.output.add_info('W', pkg, 'systemd-service-without-service_add_pre', basename)
                if not processed['post']:
                    self.output.add_info('W', pkg, 'systemd-service-without-service_add_post', basename)
                if not processed['preun']:
                    self.output.add_info('W', pkg, 'systemd-service-without-service_del_preun', basename)
                if not processed['postun']:
                    self.output.add_info('W', pkg, 'systemd-service-without-service_del_postun', basename)
