#############################################################################
# Project         : Mandriva Linux
# Module          : rpmlint
# File            : InitScriptCheck.py
# Author          : Frederic Lepied
# Created On      : Fri Aug 25 09:26:37 2000
# Purpose         : check init scripts (files in /etc/rc.d/init.d)
#############################################################################

from pathlib import Path
import re

import rpm
from rpmlint.checks.AbstractCheck import AbstractCheck
from rpmlint.helpers import readlines


chkconfig_content_regex = re.compile(r'^\s*#\s*chkconfig:\s*([-0-9]+)\s+[-0-9]+\s+[-0-9]+')
subsys_regex = re.compile(r'/var/lock/subsys/([^/"\'\s;&|]+)', re.MULTILINE)
chkconfig_regex = re.compile(r'^[^#]*(chkconfig|add-service|del-service)', re.MULTILINE)
status_regex = re.compile(r'^[^#]*status', re.MULTILINE)
reload_regex = re.compile(r'^[^#]*reload', re.MULTILINE)
lsb_tags_regex = re.compile(r'^# ([\w-]+):\s*(.*?)\s*$')
lsb_cont_regex = re.compile(r'^#(?:%s|  )(.*?)\s*$' % '\t')

LSB_KEYWORDS = ('Provides', 'Required-Start', 'Required-Stop', 'Should-Start',
                'Should-Stop', 'Default-Start', 'Default-Stop',
                'Short-Description', 'Description')
RECOMMENDED_LSB_KEYWORDS = ('Provides', 'Required-Start', 'Required-Stop',
                            'Default-Stop', 'Short-Description')


var_regex = re.compile(r'^(.*)\${?(\w+)}?(.*)$')


def shell_var_value(var, script):
    assign_regex = re.compile(r'\b' + re.escape(var) +
                              r'\s*=\s*(.+)\s*(#.*)*$', re.MULTILINE)
    res = assign_regex.search(script)
    if res:
        res2 = var_regex.search(res.group(1))
        if res2:
            if res2.group(2) == var:  # infinite loop
                return None
        return substitute_shell_vars(res.group(1), script)
    else:
        return None


def substitute_shell_vars(val, script):
    res = var_regex.search(val)
    if res:
        value = shell_var_value(res.group(2), script)
        if not value:
            value = ''
        return res.group(1) + value + \
            substitute_shell_vars(res.group(3), script)
    else:
        return val


class InitScriptCheck(AbstractCheck):

    def __init__(self, config, output):
        super().__init__(config, output)
        self.use_deflevels = self.config.configuration['UseDefaultRunlevels']
        self.use_subsys = self.config.configuration['UseVarLockSubsys']

    def check_binary(self, pkg):
        initscript_list = []
        for fname, pkgfile in pkg.files.items():

            if not fname.startswith('/etc/init.d/') and \
                    not fname.startswith('/etc/rc.d/init.d/'):
                continue

            basename = Path(fname).name
            initscript_list.append(basename)
            if pkgfile.mode & 0o500 != 0o500:
                self.output.add_info('E', pkg, 'init-script-non-executable', fname)

            if '.' in basename:
                self.output.add_info('E', pkg, 'init-script-name-with-dot', fname)

            # check chkconfig call in %post and %preun
            postin = pkg[rpm.RPMTAG_POSTIN] or \
                pkg.scriptprog(rpm.RPMTAG_POSTINPROG)
            if not postin:
                self.output.add_info('E', pkg, 'init-script-without-chkconfig-postin', fname)
            elif not chkconfig_regex.search(postin):
                self.output.add_info('E', pkg, 'postin-without-chkconfig', fname)

            preun = pkg[rpm.RPMTAG_PREUN] or \
                pkg.scriptprog(rpm.RPMTAG_PREUNPROG)
            if not preun:
                self.output.add_info('E', pkg, 'init-script-without-chkconfig-preun', fname)
            elif not chkconfig_regex.search(preun):
                self.output.add_info('E', pkg, 'preun-without-chkconfig', fname)

            status_found = False
            reload_found = False
            chkconfig_content_found = False
            subsys_regex_found = False
            in_lsb_tag = False
            in_lsb_description = False
            lastline = ''
            lsb_tags = {}
            # check common error in file content
            content = None
            try:
                content = list(readlines(pkgfile.path))
            except Exception as e:
                self.output.add_info('W', pkg, 'read-error', e)
                continue
            content_str = ''.join(content)
            for line in content:
                line = line[:-1]  # chomp
                # TODO check if there is only one line like this
                if line.startswith('### BEGIN INIT INFO'):
                    in_lsb_tag = True
                    continue
                if line.endswith('### END INIT INFO'):
                    in_lsb_tag = False
                    for kw, vals in lsb_tags.items():
                        if len(vals) != 1:
                            self.output.add_info('E', pkg, 'redundant-lsb-keyword', kw)

                    for kw in RECOMMENDED_LSB_KEYWORDS:
                        if kw not in lsb_tags:
                            self.output.add_info('W', pkg, 'missing-lsb-keyword',
                                                 '%s in %s' % (kw, fname))
                if in_lsb_tag:
                    # TODO maybe we do not have to handle this ?
                    if lastline.endswith('\\'):
                        line = lastline + line
                    else:
                        res = lsb_tags_regex.search(line)
                        if not res:
                            cres = lsb_cont_regex.search(line)
                            if not (in_lsb_description and cres):
                                in_lsb_description = False
                                self.output.add_info('E',
                                                     pkg, 'malformed-line-in-lsb-comment-block',
                                                     line)
                            else:
                                lsb_tags['Description'][-1] += \
                                    ' ' + cres.group(1)
                        else:
                            tag = res.group(1)
                            if not tag.startswith('X-') and \
                                    tag not in LSB_KEYWORDS:
                                self.output.add_info('E', pkg, 'unknown-lsb-keyword', line)
                            else:
                                in_lsb_description = (tag == 'Description')
                                if tag not in lsb_tags:
                                    lsb_tags[tag] = []
                                lsb_tags[tag].append(res.group(2))
                    lastline = line

                if not status_found and status_regex.search(line):
                    status_found = True

                if not reload_found and reload_regex.search(line):
                    reload_found = True

                res = chkconfig_content_regex.search(line)
                if res:
                    chkconfig_content_found = True
                    if self.use_deflevels:
                        if res.group(1) == '-':
                            self.output.add_info('W', pkg, 'no-default-runlevel', fname)
                    elif res.group(1) != '-':
                        self.output.add_info('W', pkg, 'service-default-enabled', fname)

                res = subsys_regex.search(line)
                if res:
                    subsys_regex_found = True
                    name = res.group(1)
                    if self.use_subsys and name != basename:
                        error = True
                        if name[0] == '$':
                            value = substitute_shell_vars(name, content_str)
                            if value == basename:
                                error = False
                        else:
                            i = name.find('}')
                            if i != -1:
                                name = name[0:i]
                                error = name != basename
                        if error and len(name):
                            if name[0] == '$':
                                self.output.add_info('W', pkg, 'incoherent-subsys', fname,
                                                     name)
                            else:
                                self.output.add_info('E', pkg, 'incoherent-subsys', fname,
                                                     name)

            if 'Default-Start' in lsb_tags:
                if ''.join(lsb_tags['Default-Start']):
                    self.output.add_info('W', pkg, 'service-default-enabled', fname)

            if not status_found:
                self.output.add_info('E', pkg, 'no-status-entry', fname)
            if not reload_found:
                self.output.add_info('W', pkg, 'no-reload-entry', fname)
            if not chkconfig_content_found:
                self.output.add_info('E', pkg, 'no-chkconfig-line', fname)
            if not subsys_regex_found and self.use_subsys:
                self.output.add_info('E', pkg, 'subsys-not-used', fname)
            elif subsys_regex_found and not self.use_subsys:
                self.output.add_info('E', pkg, 'subsys-unsupported', fname)

        if len(initscript_list) == 1:
            pkgname = re.sub('-sysvinit$', '', pkg.name.lower())
            goodnames = (pkgname, pkgname + 'd')
            if initscript_list[0] not in goodnames:
                self.output.add_info('W', pkg, 'incoherent-init-script-name',
                                     initscript_list[0], str(goodnames))
