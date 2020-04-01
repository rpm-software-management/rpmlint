#############################################################################
# Project         : Mandriva Linux
# Module          : rpmlint
# File            : PostCheck.py
# Author          : Frederic Lepied
# Created On      : Wed Jul  5 13:30:17 2000
# Purpose         : Check post/pre scripts
#############################################################################

import os
import re
import subprocess
import tempfile

import rpm
from rpmlint import pkg as Pkg
from rpmlint.checks.AbstractCheck import AbstractCheck
from rpmlint.helpers import byte_to_string, ENGLISH_ENVIROMENT


# shells that grok the -n switch for debugging
syntaxcheck_shells = ('/bin/sh', '/bin/bash')

percent_regex = re.compile(r'^[^#]*%{?\w{3,}', re.MULTILINE)
bracket_regex = re.compile(r'^[^#]*if\s+[^ :\]]\]', re.MULTILINE)
home_regex = re.compile(r'[^a-zA-Z]+~/|\${?HOME(\W|$)', re.MULTILINE)
dangerous_command_regex = re.compile(r'(^|[;\|`]|&&|$\()\s*(?:\S*/s?bin/)?(cp|mv|ln|tar|rpm|chmod|chown|rm|cpio|install|perl|userdel|groupdel)\s', re.MULTILINE)
selinux_regex = re.compile(r'(^|[;\|`]|&&|$\()\s*(?:\S*/s?bin/)?(chcon|runcon)\s', re.MULTILINE)
single_command_regex = re.compile(r'^[ %s]*([^ %s]+)[ %s]*$' % (('\n',) * 3))
tmp_regex = re.compile(r'^[^#]*\s(/var)?/tmp', re.MULTILINE)
menu_regex = re.compile(r'^/usr/lib/menu/|^/etc/menu-methods/|^/usr/share/applications/')
bogus_var_regex = re.compile(r'(\${?RPM_BUILD_(ROOT|DIR)}?)')

prereq_assoc = (
    # ['chkconfig', ('chkconfig', '/sbin/chkconfig')],
    ['chkfontpath', ('chkfontpath', '/usr/sbin/chkfontpath')],
    ['rpm-helper', ('rpm-helper',)],
)

for p in prereq_assoc:
    p[0] = re.compile(r'^[^#]+' + p[0], re.MULTILINE)

# pychecker fix
del p


def incorrect_shell_script(prog, shellscript):
    return check_syntax_script(prog, '-n', shellscript)


def incorrect_perl_script(prog, perlscript):
    return check_syntax_script(prog, '-wc', perlscript)


def check_syntax_script(prog, commandline, script):
    if not script:
        return False
    if isinstance(script, str):
        script = script.encode('utf-8')
    # TODO: test that 'prog' is available/executable
    tmpfd, tmpname = tempfile.mkstemp(prefix='rpmlint.')
    tmpfile = os.fdopen(tmpfd, 'wb')
    try:
        tmpfile.write(script)
        tmpfile.close()
        ret = subprocess.run((prog, commandline, tmpname), env=ENGLISH_ENVIROMENT)
    finally:
        tmpfile.close()
        os.remove(tmpname)
    return ret.returncode


class PostCheck(AbstractCheck):

    def __init__(self, config, output):
        super().__init__(config, output)
        self.valid_shells = config.configuration['ValidShells']
        self.empty_shells = config.configuration['ValidEmptyShells']
        post_details_dict = {
            'postin-without-ghost-file-creation':
            """A file tagged as ghost is not created during %prein nor during %postin.""",
        }
        for scriptlet in map(lambda x: '%' + x, Pkg.RPM_SCRIPTLETS):
            post_details_dict.update({
                'one-line-command-in-%s' % scriptlet:
                """You should use %s -p <command> instead of using:

                %s
                <command>

                It will avoid the fork of a shell interpreter to execute your command as
                well as allows rpm to automatically mark the dependency on your command
                for the execution of the scriptlet.""" % (scriptlet, scriptlet),

                'percent-in-%s' % scriptlet:
                """The %s scriptlet contains a '%%' in a context which might indicate it being
                fallout from an rpm macro/variable which was not expanded during build.
                Investigate whether this is the case and fix if appropriate.""" % scriptlet,

                'spurious-bracket-in-%s' % scriptlet:
                """The %s scriptlet contains an 'if []' construct without a space before
                the ']'.""" % scriptlet,

                'forbidden-selinux-command-in-%s' % scriptlet:
                """A command which requires intimate knowledge about a specific SELinux
                policy type was found in the scriptlet. These types are subject to change
                on a policy version upgrade. Use the restorecon command which queries the
                currently loaded policy for the correct type instead.""",

                'non-empty-%s' % scriptlet:
                """Scriptlets for the interpreter mentioned in the message should be empty.
                One common case where they are unintentionally not is when the specfile
                contains comments after the scriptlet and before the next section. Review
                and clean up the scriptlet contents if appropriate.""",
            })
        self.output.error_details.update(post_details_dict)

    def check_binary(self, pkg):
        prereq = [x[0] for x in pkg.prereq]

        for tag in Pkg.SCRIPT_TAGS:
            script = pkg[tag[0]]

            if not isinstance(script, list):
                prog = pkg.scriptprog(tag[1])
                if prog:
                    prog = prog.split()[0]
                self.check_aux(pkg, prog, pkg.header[tag[0]],
                               tag[2], prereq)
            else:
                prog = pkg[tag[1]]
                for idx in range(0, len(prog)):
                    self.check_aux(
                        pkg, prog[idx],
                        pkg.header[tag[0]][idx], tag[2], prereq)

        ghost_files = pkg.ghost_files
        if ghost_files:
            postin = pkg[rpm.RPMTAG_POSTIN]
            prein = pkg[rpm.RPMTAG_PREIN]
            for f in ghost_files:
                if f in pkg.missingok_files:
                    continue
                if not postin and not prein:
                    self.output.add_info('W', pkg, 'ghost-files-without-postin')
                if (not postin or f not in postin) and \
                        (not prein or f not in prein):
                    self.output.add_info('W', pkg,
                                         'postin-without-ghost-file-creation', f)

    def check_aux(self, pkg, prog, script, tag, prereq):
        files = pkg.files
        if script:
            script_str = byte_to_string(script)
            if prog:
                if prog not in self.valid_shells:
                    self.output.add_info('E', pkg, 'invalid-shell-in-' + tag, prog)
                if prog in self.empty_shells:
                    self.output.add_info('E', pkg, 'non-empty-' + tag, prog)
            if prog in syntaxcheck_shells or prog == '/usr/bin/perl':
                if percent_regex.search(script_str):
                    self.output.add_info('W', pkg, 'percent-in-' + tag)
                if bracket_regex.search(script_str):
                    self.output.add_info('W', pkg, 'spurious-bracket-in-' + tag)
                res = dangerous_command_regex.search(script_str)
                if res:
                    self.output.add_info('W', pkg, 'dangerous-command-in-' + tag,
                                         res.group(2))
                res = selinux_regex.search(script_str)
                if res:
                    self.output.add_info('E', pkg, 'forbidden-selinux-command-in-' + tag,
                                         res.group(2))

                if 'update-menus' in script_str:
                    menu_error = True
                    for f in files:
                        if menu_regex.search(f):
                            menu_error = False
                            break
                    if menu_error:
                        self.output.add_info('E', pkg,
                                             'update-menus-without-menu-file-in-' + tag)
                if tmp_regex.search(script_str):
                    self.output.add_info('E', pkg, 'use-tmp-in-' + tag)
                for c in prereq_assoc:
                    if c[0].search(script_str):
                        found = False
                        for p in c[1]:
                            if p in prereq or p in files:
                                found = True
                                break
                        if not found:
                            self.output.add_info('E', pkg, 'no-prereq-on', c[1][0])

            if prog in syntaxcheck_shells:
                if incorrect_shell_script(prog, script):
                    self.output.add_info('E', pkg, 'shell-syntax-error-in-' + tag)
                if home_regex.search(script_str):
                    self.output.add_info('E', pkg, 'use-of-home-in-' + tag)
                res = bogus_var_regex.search(script_str)
                if res:
                    self.output.add_info('W', pkg, 'bogus-variable-use-in-' + tag,
                                         res.group(1))

            if prog == '/usr/bin/perl':
                if incorrect_perl_script(prog, script):
                    self.output.add_info('E', pkg, 'perl-syntax-error-in-' + tag)
            elif prog.endswith('sh'):
                res = single_command_regex.search(script_str)
                if res:
                    self.output.add_info('W', pkg, 'one-line-command-in-' + tag,
                                         res.group(1))

        elif prog not in self.empty_shells and prog in self.valid_shells:
            self.output.add_info('W', pkg, 'empty-' + tag)
