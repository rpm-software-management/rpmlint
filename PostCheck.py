# -*- coding: utf-8 -*-
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

import rpm

from Filter import addDetails, printError, printWarning
import AbstractCheck
import Config
import Pkg


RPM_SCRIPTLETS = ('pre', 'post', 'preun', 'postun', 'pretrans', 'posttrans',
                  'trigger', 'triggerin', 'triggerprein', 'triggerun',
                  'triggerun', 'triggerpostun', 'verifyscript')

DEFAULT_VALID_SHELLS = ('<lua>',
                        '/bin/sh',
                        '/bin/bash',
                        '/sbin/sash',
                        '/usr/bin/perl',
                        '/sbin/ldconfig',
                        )

DEFAULT_EMPTY_SHELLS = ('/sbin/ldconfig',
                        )

valid_shells = Config.getOption('ValidShells', DEFAULT_VALID_SHELLS)
empty_shells = Config.getOption('ValidEmptyShells', DEFAULT_EMPTY_SHELLS)
# shells that grok the -n switch for debugging
syntaxcheck_shells = ('/bin/sh', '/bin/bash')

percent_regex = re.compile('^[^#]*%{?\w{3,}', re.MULTILINE)
bracket_regex = re.compile('^[^#]*if\s+[^ :\]]\]', re.MULTILINE)
home_regex = re.compile('[^a-zA-Z]+~/|\${?HOME(\W|$)', re.MULTILINE)
dangerous_command_regex = re.compile("(^|[;\|`]|&&|$\()\s*(?:\S*/s?bin/)?(cp|mv|ln|tar|rpm|chmod|chown|rm|cpio|install|perl|userdel|groupdel)\s", re.MULTILINE)
selinux_regex = re.compile("(^|[;\|`]|&&|$\()\s*(?:\S*/s?bin/)?(chcon|runcon)\s", re.MULTILINE)
single_command_regex = re.compile("^[ \n]*([^ \n]+)[ \n]*$")
tmp_regex = re.compile('^[^#]*\s(/var)?/tmp', re.MULTILINE)
menu_regex = re.compile('^/usr/lib/menu/|^/etc/menu-methods/|^/usr/share/applications/')
bogus_var_regex = re.compile('(\${?RPM_BUILD_(ROOT|DIR)}?)')

prereq_assoc = (
    #['chkconfig', ('chkconfig', '/sbin/chkconfig')],
    ['chkfontpath', ('chkfontpath', '/usr/sbin/chkfontpath')],
    ['rpm-helper', ('rpm-helper',)],
    )

for p in prereq_assoc:
    p[0] = re.compile('^[^#]+' + p[0], re.MULTILINE)

# pychecker fix
del p

script_tags = [
    (rpm.RPMTAG_PREIN,          rpm.RPMTAG_PREINPROG,         '%pre'),
    (rpm.RPMTAG_POSTIN,         rpm.RPMTAG_POSTINPROG,        '%post'),
    (rpm.RPMTAG_PREUN,          rpm.RPMTAG_PREUNPROG,         '%preun'),
    (rpm.RPMTAG_POSTUN,         rpm.RPMTAG_POSTUNPROG,        '%postun'),
    (rpm.RPMTAG_TRIGGERSCRIPTS, rpm.RPMTAG_TRIGGERSCRIPTPROG, '%trigger'),
    (rpm.RPMTAG_PRETRANS,       rpm.RPMTAG_PRETRANSPROG,      '%pretrans'),
    (rpm.RPMTAG_POSTTRANS,      rpm.RPMTAG_POSTTRANSPROG,     '%posttrans'),
    (rpm.RPMTAG_VERIFYSCRIPT,   rpm.RPMTAG_VERIFYSCRIPTPROG,  '%verifyscript'),
    ]


def incorrect_shell_script(prog, shellscript):
    return check_syntax_script(prog, '-n', shellscript)


def incorrect_perl_script(prog, perlscript):
    return check_syntax_script(prog, '-wc', perlscript)


def check_syntax_script(prog, commandline, script):
    if not script:
        return False
    # TODO: test that "prog" is available/executable
    tmpfile, tmpname = Pkg.mktemp()
    try:
        tmpfile.write(script)
        tmpfile.close()
        ret = Pkg.getstatusoutput((prog, commandline, tmpname))
    finally:
        tmpfile.close()
        os.remove(tmpname)
    return ret[0]


class PostCheck(AbstractCheck.AbstractCheck):

    def __init__(self):
        AbstractCheck.AbstractCheck.__init__(self, 'PostCheck')

    def check_binary(self, pkg):
        prereq = [x[0] for x in pkg.prereq()]
        files = pkg.files()

        for tag in script_tags:
            script = pkg[tag[0]]

            if not isinstance(script, list):
                prog = pkg.scriptprog(tag[1])
                if prog:
                    prog = prog.split()[0]
                self.check_aux(pkg, files, prog, script, tag[2], prereq)
            else:
                prog = pkg[tag[1]]
                for idx in range(0, len(prog)):
                    self.check_aux(
                        pkg, files, prog[idx], script[idx], tag[2], prereq)

        ghost_files = pkg.ghostFiles()
        if ghost_files:
            postin = pkg[rpm.RPMTAG_POSTIN]
            prein = pkg[rpm.RPMTAG_PREIN]
            for f in ghost_files:
                if f in pkg.missingOkFiles():
                    continue
                if not postin and not prein:
                    printWarning(pkg, 'ghost-files-without-postin')
                if (not postin or f not in postin) and \
                        (not prein or f not in prein):
                    printWarning(pkg,
                                 'postin-without-ghost-file-creation', f)

    def check_aux(self, pkg, files, prog, script, tag, prereq):
        if script:
            if prog:
                if prog not in valid_shells:
                    printError(pkg, 'invalid-shell-in-' + tag, prog)
                if prog in empty_shells:
                    printError(pkg, 'non-empty-' + tag, prog)
            if prog in syntaxcheck_shells or prog == '/usr/bin/perl':
                if percent_regex.search(script):
                    printWarning(pkg, 'percent-in-' + tag)
                if bracket_regex.search(script):
                    printWarning(pkg, 'spurious-bracket-in-' + tag)
                res = dangerous_command_regex.search(script)
                if res:
                    printWarning(pkg, 'dangerous-command-in-' + tag,
                                 res.group(2))
                res = selinux_regex.search(script)
                if res:
                    printError(pkg, 'forbidden-selinux-command-in-' + tag,
                               res.group(2))

                if 'update-menus' in script:
                    menu_error = True
                    for f in files:
                        if menu_regex.search(f):
                            menu_error = False
                            break
                    if menu_error:
                        printError(pkg, 'update-menus-without-menu-file-in-' +
                                   tag)
                if tmp_regex.search(script):
                    printError(pkg, 'use-tmp-in-' + tag)
                for c in prereq_assoc:
                    if c[0].search(script):
                        found = False
                        for p in c[1]:
                            if p in prereq or p in files:
                                found = True
                                break
                        if not found:
                            printError(pkg, 'no-prereq-on', c[1][0])

            if prog in syntaxcheck_shells:
                if incorrect_shell_script(prog, script):
                    printError(pkg, 'shell-syntax-error-in-' + tag)
                if home_regex.search(script):
                    printError(pkg, 'use-of-home-in-' + tag)
                res = bogus_var_regex.search(script)
                if res:
                    printWarning(pkg, 'bogus-variable-use-in-' + tag,
                                 res.group(1))

            if prog == '/usr/bin/perl':
                if incorrect_perl_script(prog, script):
                    printError(pkg, 'perl-syntax-error-in-' + tag)
            elif prog.endswith('sh'):
                res = single_command_regex.search(script)
                if res:
                    printWarning(pkg, 'one-line-command-in-' + tag,
                                 res.group(1))

        elif prog not in empty_shells and prog in valid_shells:
            printWarning(pkg, 'empty-' + tag)

# Create an object to enable the auto registration of the test
check = PostCheck()

# Add information about checks
addDetails(
'postin-without-ghost-file-creation',
'''A file tagged as ghost is not created during %prein nor during %postin.''',
)
for scriptlet in map(lambda x: '%' + x, RPM_SCRIPTLETS):
    addDetails(
'one-line-command-in-%s' % scriptlet,
'''You should use %s -p <command> instead of using:

%s
<command>

It will avoid the fork of a shell interpreter to execute your command as
well as allows rpm to automatically mark the dependency on your command
for the execution of the scriptlet.''' % (scriptlet, scriptlet),

'percent-in-%s' % scriptlet,
'''The %s scriptlet contains a "%%" in a context which might indicate it being
fallout from an rpm macro/variable which was not expanded during build.
Investigate whether this is the case and fix if appropriate.''' % scriptlet,

'spurious-bracket-in-%s' % scriptlet,
'''The %s scriptlet contains an "if []" construct without a space before
the "]".''' % scriptlet,

'forbidden-selinux-command-in-%s' % scriptlet,
'''A command which requires intimate knowledge about a specific SELinux
policy type was found in the scriptlet. These types are subject to change
on a policy version upgrade. Use the restorecon command which queries the
currently loaded policy for the correct type instead.''',

'non-empty-%s' % scriptlet,
'''Scriptlets for the interpreter mentioned in the message should be empty.
One common case where they are unintentionally not is when the specfile
contains comments after the scriptlet and before the next section. Review
and clean up the scriptlet contents if appropriate.''',
)

# PostCheck.py ends here

# Local variables:
# indent-tabs-mode: nil
# py-indent-offset: 4
# End:
# ex: ts=4 sw=4 et
