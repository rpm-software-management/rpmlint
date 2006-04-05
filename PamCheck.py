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
import rpm
import re,os,time,subprocess
import Config
pam_re=re.compile('/etc/pam\.d/.*')
pam_stack_re=re.compile('pam_stack.so\s*service')

class PamCheck(AbstractCheck.AbstractCheck):

    def __init__(self):
        AbstractCheck.AbstractCheck.__init__(self, "PamCheck")

    def check(self, pkg):
        if pkg.isSource():
            return
        dirname=pkg.dirName()
        pam_files=[]
        for f in pkg.files().keys():
            if pam_re.match(f):
                pam_files.append(f)
        for i in pam_files:
            self.check_pam_file(pkg, dirname, i)

    def check_pam_file(self, pkg, directory, filename):
        f = open(directory + filename)
        for l in f.readlines():
            if pam_stack_re.search(l):
                printError(pkg, 'use-old-pam-stack',filename)
        f.close()
check=PamCheck()

if Config.info:
    addDetails(
        'use-old-pam-stack',
        '''Update pam file to use include instead of pam_stack.''',)

