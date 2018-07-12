# -*- coding: utf-8 -*-
#############################################################################
# Project         : Mandriva Linux
# Module          : rpmlint
# File            : NamingPolicyCheck.py
# Author          : Michael Scherer
# Created On      : Mon May 19 11:25:37 2003
# Purpose         : Check package names according to their content.
#############################################################################

import re

import rpmlint.AbstractCheck as AbstractCheck
from rpmlint.Filter import addDetails, printWarning

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

simple_naming_policy_re = re.compile(r'\^[a-zA-Z1-9-_]*$')


class NamingPolicyNotAppliedException(Exception):
    pass


class NamingPolicyCheck(AbstractCheck.AbstractCheck):
    checks_ = []

    def __init__(self):
        AbstractCheck.AbstractCheck.__init__(self, "NamingPolicyCheck")

    def add_check(self, pkg_name, name_re, file_re):
        c = {}
        c['pkg_name'] = pkg_name
        c['name_re'] = re.compile(name_re)
        c['file_re'] = re.compile(file_re)
        self.checks_.append(c)

        if simple_naming_policy_re.search(name_re):
            details = "Its name should begin with " + name_re[1:]
        else:
            details = "Its name should match the regular expression " + name_re

        addDetails(pkg_name + '-naming-policy-not-applied',
                   "This package doesn't respect the naming policy for %s "
                   "packages.\n%s." % (pkg_name, details))

    def check_binary(self, pkg):
        files = pkg.files()
        if not files:
            return
        try:
            # check for files then
            for c in self.checks_:
                for f in files:
                    if c['file_re'].search(f) and \
                            not c['name_re'].search(pkg.name):
                        raise NamingPolicyNotAppliedException
        except NamingPolicyNotAppliedException:
            printWarning(pkg, c['pkg_name'] + '-naming-policy-not-applied', f)


check = NamingPolicyCheck()

#
# these are the check currently implemented.
#
# first argument is the name of the check, printed by the warning.
#   ex : xmms.
#
# secund argument is the regular expression of the naming policy.
#   ex: xmms plugin should be named xmms-name_of_plugin.
#
# third is the path of the file that should contains a package to be related to
# the naming scheme.
#   ex: xmms plugin are put under /usr/lib/xmms/
#
# the module is far from being perfect since you need to check this file for
# the naming file.
# if somone as a elegant solution, I will be happy to implement and test it.

check.add_check('xmms', '^xmms(-|$)', '^/usr/lib(64)?/xmms/')
check.add_check('python', '^python(-|$)', '^/usr/lib(64)?/python[1-9](-[1-9])?')
check.add_check('perl5', '^perl(-|$)', '^/usr/lib(64)?/perl5/vendor_perl')
check.add_check('apache2', '^apache2-mod_', '^/usr/lib(64)?/apache2-')
check.add_check('fortune', '^fortune(-|$)', '^/usr/share/games/fortunes/')
check.add_check('php', '^php(-|$)', '/usr/lib(64)?/php/extensions/')
check.add_check('ruby', '^ruby(-|$)', '/usr/lib(64)?/ruby/[1-9](-[1-9])?/')
check.add_check('ocaml', '^ocaml(-|$)', '/usr/lib(64)?/ocaml/')

# these exception should be added
# apache2 => apache2-devel
#            apache2-modules
# ruby => apache2-mod_ruby
#         ruby

# NamingPolicyCheck.py ends here
