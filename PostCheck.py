#############################################################################
# Project         : Mandrakelinux
# Module          : rpmlint
# File            : PostCheck.py
# Version         : $Id$
# Author          : Frederic Lepied
# Created On      : Wed Jul  5 13:30:17 2000
# Purpose         : Check post/pre scripts
#############################################################################

from Filter import *
import AbstractCheck
import rpm
import re
import os
import commands
import string
import types

DEFAULT_VALID_SHELLS=('/bin/sh',
                      '/bin/bash',
                      '/sbin/sash',
                      '/usr/bin/perl',
                      '/sbin/ldconfig',
                      )

DEFAULT_EMPTY_SHELLS=('/sbin/ldconfig',
                     )

extract_dir=Config.getOption('ExtractDir', '/tmp')
valid_shells=Config.getOption('ValidShells', DEFAULT_VALID_SHELLS)
empty_shells=Config.getOption('ValidEmptyShells', DEFAULT_EMPTY_SHELLS)

braces_regex=re.compile('^[^#]*%', re.MULTILINE)
double_braces_regex=re.compile('%%', re.MULTILINE)
bracket_regex=re.compile('^[^#]*if.*[^ :\]]\]', re.MULTILINE)
home_regex=re.compile('[^a-zA-Z]+~/|\$HOME', re.MULTILINE)
dangerous_command_regex=re.compile("(^|\s|;|/bin/|\|)(cp|mv|ln|tar|rpm|chmod|chown|rm|cpio|install|perl)\s", re.MULTILINE)
single_command_regex=re.compile("^[ \n]*([^ \n]+)[ \n]*$")
update_menu_regex=re.compile('update-menus', re.MULTILINE)
tmp_regex=re.compile('\s(/var)?/tmp', re.MULTILINE)
menu_regex=re.compile('^/usr/lib/menu/|^/etc/menu-methods/')
bogus_var_regex=re.compile('(\${?RPM_BUILD_(ROOT|DIR)}?)')

prereq_assoc = (
#    ['chkconfig', ('chkconfig', '/sbin/chkconfig')],
    ['chkfontpath', ('chkfontpath', '/usr/sbin/chkfontpath')],
    ['rpm-helper', ('rpm-helper',)],
    )

for p in prereq_assoc:
    p[0] = re.compile('^[^#]+' + p[0], re.MULTILINE)
    
def incorrect_shell_script(shellscript):
    tmpfile = '%s/.bash-script.%d' % (extract_dir, os.getpid())
    if not shellscript:
        return 0
    file=open(tmpfile, 'w')
    file.write(shellscript)
    file.close()
    ret=commands.getstatusoutput('/bin/bash -n %s' % tmpfile)
    os.remove(tmpfile)
    return ret[0]

def incorrect_perl_script(perlscript):
    tmpfile = '%s/.perl-script.%d' % (extract_dir, os.getpid())
    if not perlscript:
        return 0
    file=open(tmpfile, 'w')
    file.write(perlscript)
    file.close()
    ret=commands.getstatusoutput('/usr/bin/perl -wc %s' % tmpfile)
    os.remove(tmpfile)
    return ret[0]

class PostCheck(AbstractCheck.AbstractCheck):
    
    def __init__(self):
        AbstractCheck.AbstractCheck.__init__(self, 'PostCheck')

    def check(self, pkg):
	# Check only binary package
	if pkg.isSource():
	    return

        menu_error=0
        prereq=map(lambda x: x[0], pkg.prereq())
        files=pkg.files().keys()
        
        for tag in ((rpm.RPMTAG_PREIN, rpm.RPMTAG_PREINPROG, '%pre'),
                    (rpm.RPMTAG_POSTIN, rpm.RPMTAG_POSTINPROG, '%post'),
                    (rpm.RPMTAG_PREUN, rpm.RPMTAG_PREUNPROG, '%preun'),
                    (rpm.RPMTAG_POSTUN, rpm.RPMTAG_POSTUNPROG, '%postun'),
                    (rpm.RPMTAG_TRIGGERSCRIPTS, rpm.RPMTAG_TRIGGERSCRIPTPROG, '%trigger'),
                    ):
            script = pkg[tag[0]]
            prog = pkg[tag[1]]

            if type(script) != types.ListType:
                self.check_aux(pkg, files, prog, script, tag, prereq)
            else:
                for idx in range(0, len(prog)):
                    self.check_aux(pkg, files, prog[idx], script[idx], tag, prereq)
                     
        ghost_files=pkg.ghostFiles()
        if ghost_files:
            postin=pkg[rpm.RPMTAG_POSTIN]
            prein=pkg[rpm.RPMTAG_PREIN]
            if not postin and not prein:
                printWarning(pkg, 'ghost-files-without-postin')
            else:
                for f in ghost_files:
                    if (not postin or string.find(postin, f) == -1) and \
                       (not prein or string.find(prein, f) == -1):
                        printWarning(pkg, 'postin-without-ghost-file-creation', f)

    def check_aux(self, pkg, files, prog, script, tag, prereq):
        if script:
            if prog:
                if not prog in valid_shells:
                    printError(pkg, 'invalid-shell-in-' + tag[2], prog)
                if prog in empty_shells:
                    printError(pkg, 'non-empty-' + tag[2], prog)
            if prog == '/bin/sh' or prog == '/bin/bash' or prog == '/usr/bin/perl':
                if braces_regex.search(script) and not double_braces_regex.search(script):
                    printWarning(pkg, 'percent-in-' + tag[2])
                if bracket_regex.search(script):
                    printWarning(pkg, 'spurious-bracket-in-' + tag[2])
                res=dangerous_command_regex.search(script)
                if res:
                    printWarning(pkg, 'dangerous-command-in-' + tag[2], res.group(2))
                if update_menu_regex.search(script):
                    menu_error=1
                    for f in files:
                        if menu_regex.search(f):
                            menu_error=0
                            break
                    if menu_error:
                        printError(pkg, 'update-menus-without-menu-file-in-' + tag[2])
                if tmp_regex.search(script):
                    printError(pkg, 'use-tmp-in-' + tag[2])
                for c in prereq_assoc:
                    if c[0].search(script):
                        found=0
                        for p in c[1]:
                            if p in prereq or p in files:
                                found=1
                                break
                        if not found:
                            printError(pkg, 'no-prereq-on', c[1][0])
                            
            if prog == '/bin/sh' or prog == '/bin/bash':
                if incorrect_shell_script(script):
                    printError(pkg, 'shell-syntax-error-in-' + tag[2])
                if home_regex.search(script):
                    printError(pkg, 'use-of-home-in-' + tag[2])
                res=bogus_var_regex.search(script)
                if res:
                    printWarning(pkg, 'bogus-variable-use-in-' + tag[2], res.group(1))

            if prog == '/usr/bin/perl':
                if incorrect_perl_script(script):
                    printError(pkg, 'perl-syntax-error-in-' + tag[2])
                    
            res=single_command_regex.search(script)
            if res:
                printWarning(pkg, 'one-line-command-in-' + tag[2], res.group(1))
        else:
            if prog not in empty_shells and prog in valid_shells:
                printWarning(pkg, 'empty-' + tag[2])

# Create an object to enable the auto registration of the test
check=PostCheck()

# Add information about checks
if Config.info:
    addDetails(
'one-line-command-in-%post',
'''You should use %post -p <command> instead of using:

%post
<command>

It will avoid the fork of a shell interpreter to execute your command as
well as allows rpm to automatically mark the dependency on your command.''',

'one-line-command-in-%postun',
'''You should use %postun -p <command> instead of using:

%postun
<command>

It will avoid the fork of a shell interpreter to execute your command as
well as allows rpm to automatically mark the dependency on your command.''',

'one-line-command-in-%pre',
'''You should use %pre -p <command> instead of using:

%pre
<command>

It will avoid the fork of a shell interpreter to execute your command as
well as allows rpm to automatically mark the dependency on your command.''',

'one-line-command-in-%preun',
'''You should use %preun -p <command> instead of using:

%preun
<command>

It will avoid the fork of a shell interpreter to execute your command as
well as allows rpm to automatically mark the dependency on your command.''',

'spurious-bracket-in-%pre',
'''The %pre scriptlet contains an if [] construction without a space before the
].''',

'spurious-bracket-in-%post',
'''The %post scriptlet contains an if [] construction without a space before the
].''',

'spurious-bracket-in-%preun',
'''The %preun scriptlet contains an if [] construction without a space before the
].''',

'spurious-bracket-in-%postun',
'''The %postun scriptlet contains an if [] construction without a space before the
].''',

'postin-without-ghost-file-creation',
'''A file tagged as ghost is not created during %prein nor during %postin.''',
)

# PostCheck.py ends here
