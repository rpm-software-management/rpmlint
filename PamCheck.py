#---------------------------------------------------------------
# Project         : Mandriva Linux
# Module          : rpmlint
# File            : PamCheck.py
# Version         : $Id: /local/personal/PamCheck.py 4977 2006-01-31T09:29:13.664059Z misc  $
# Author          : Michael Scherer
# Created On      : 031/01/2006
# Purpose         : Apply pam policy
#---------------------------------------------------------------

from Filter import *
import AbstractCheck
import re
import Config
pam_stack_re=re.compile('pam_stack.so\s*service')

class PamCheck(AbstractCheck.AbstractFilesCheck):
    def __init__(self):
        AbstractCheck.AbstractFilesCheck.__init__(self, "PamCheck", "/etc/pam\.d/.*")
    
    def check_file(self, pkg, filename):
        f = open(pkg.dirName() + filename)
        for l in f.readlines():
            l = re.sub('#.*', '', l)
            if pam_stack_re.search(l):
                printError(pkg, 'use-old-pam-stack',filename)
        f.close()

check=PamCheck()

if Config.info:
    addDetails(
        'use-old-pam-stack',
        '''Update pam file to use include instead of pam_stack.''',)

