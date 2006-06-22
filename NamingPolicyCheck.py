#---------------------------------------------------------------
# Project         : Mandriva Linux
# Module          : rpmlint
# File            : NamingPolicyCheck.py
# Version         : $Id$
# Author          : Michael Scherer
# Created On      : Mon May 19 11:25:37 2003
# Purpose         : Check package names according to their content.
#---------------------------------------------------------------

from Filter import *
import AbstractCheck
import re
import Config

# could be added.
#
# zope
# abiword2
# alsaplayer-plugin-input
# emacs
# gstreamer
# nautilus
# vlc-plugin
# XFree
# xine

executable_re=re.compile('^(/usr)?/(s?bin|games)/\S+')
simple_naming_policy_re=re.compile('\^[a-zA-Z1-9-_]*$');

class NamingPolicyNotAppliedException(Exception):
    pass

class NamingPolicyCheck(AbstractCheck.AbstractCheck):
    checks_=[]

    def __init__(self):
        AbstractCheck.AbstractCheck.__init__(self, "NamingPolicyCheck")

    def add_check(self,pkg_name,name_re,file_re,exception):
        c={}
        c['pkg_name']=pkg_name
        c['name_re']=re.compile(name_re)
        c['file_re']=re.compile(file_re)
        c['exception']=exception
        self.checks_.append(c)
        if Config.info:
            if simple_naming_policy_re.search(name_re):
                details="The name sould begin with " + name_re[1:]
            else:
                details="The name should match this regular expression " + name_re

            addDetails(pkg_name + '-naming-policy-not-applied',
                       "This package doesn't respect the naming policy.\n"
                       + details + ".\nIt should only be used for separate packages modules.")

    def check(self, pkg):
        if pkg.isSource():
            return
        files = pkg.files().keys()
        if not files:
            return
        try:
            # check for binaries first
            executables=0
            for f in files:
                if executable_re.search(f):
                    executables=1
                    break

            # check for files then
            for c in self.checks_:
                exception=0
                if c['exception'] and executables:
                    exception=1

                for f in files:
                    if c['file_re'].search(f) and not c['name_re'].search(pkg.name) and not exception:
                        raise NamingPolicyNotAppliedException
        except NamingPolicyNotAppliedException:
            printWarning(pkg, c['pkg_name'] + '-naming-policy-not-applied', f)

check=NamingPolicyCheck()

#
# these are the check currently impleted.
#
# first argument is the name of the check, printed by the warning.
#   ex : xmms.
#
# secund argument is the regular expression of the naming policy.
#   ex: xmms plugin should be named xmms-name_of_plugin.
#
# third is the path of the file that should contains a package to be related to the naming scheme.
#   ex: xmms plugin are put under /usr/lib/xmms/
#
# fourth is a boolean for excepting packages with any executable in path of the naming scheme
#   ex: a perl package with files both in /usr/bin and in /usr/lib/perl5 can be either a module with exemple script, of a perl programs with some personal modules
#
# the module is far from being perfect since you need to check this file for the naming file.
#
# the module is far from being perfect since you need to check this file for the naming file.
# if somone as a elegant solution, I will be happy to implement and test it.


check.add_check('xmms', '^xmms-', '^/usr/lib/xmms/', 0)
check.add_check('python', '^python-', '^/usr/lib/python[1-9](-[1-9])?', 1)
check.add_check('perl5', '^perl-', '^/usr/lib/perl5/vendor_perl', 1)
check.add_check('apache2', '^apache2-mod_', '^/usr/lib/apache2-', 0)
check.add_check('fortune', '^fortune-', '^/usr/share/games/fortunes/', 0)
check.add_check('php', '^php-', '/usr/lib/php/extensions/', 1)
check.add_check('ruby', '^ruby-', '/usr/lib/ruby/[1-9](-[1-9])?/', 1)
check.add_check('ocaml', '^ocaml-', '/usr/lib/ocaml/', 1)

# these exception should be added
# apache2 => apache2-devel
#            apache2-modules
# ruby => apache2-mod_ruby
#         ruby

# NamingPolicyCheck.py ends here

# Local variables:
# indent-tabs-mode: nil
# py-indent-offset: 4
# End:
# ex: ts=4 sw=4 et
