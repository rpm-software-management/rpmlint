#############################################################################
# Project         : Mandriva Linux
# Module          : rpmlint
# File            : NamingPolicyCheck.py
# Author          : Michael Scherer
# Created On      : Mon May 19 11:25:37 2003
# Purpose         : Check package names according to their content.
#############################################################################

import re

from rpmlint.checks.AbstractCheck import AbstractCheck


class NamingPolicyNotAppliedException(Exception):
    pass


class NamingPolicyCheck(AbstractCheck):
    simple_naming_policy_re = re.compile(r'\^[a-zA-Z1-9-_]*$')
    checks_ = []

    def __init__(self, config, output):
        super().__init__(config, output)
        # TODO: rewrite this sanely
        self.add_check('xmms', '^xmms(-|$)', '^/usr/lib(64)?/xmms/')
        self.add_check('python', '^python(-|$)', '^/usr/lib(64)?/python[1-9](-[1-9])?')
        self.add_check('perl5', '^perl(-|$)', '^/usr/lib(64)?/perl5/vendor_perl')
        self.add_check('apache2', '^apache2-mod_', '^/usr/lib(64)?/apache2-')
        self.add_check('fortune', '^fortune(-|$)', '^/usr/share/games/fortunes/')
        self.add_check('php', '^php(-|$)', '/usr/lib(64)?/php/extensions/')
        self.add_check('ruby', '^ruby(-|$)', '/usr/lib(64)?/ruby/[1-9](-[1-9])?/')
        self.add_check('ocaml', '^ocaml(-|$)', '/usr/lib(64)?/ocaml/')

    def add_check(self, pkg_name, name_re, file_re):
        c = {}
        c['pkg_name'] = pkg_name
        c['name_re'] = re.compile(name_re)
        c['file_re'] = re.compile(file_re)
        self.checks_.append(c)

        if self.simple_naming_policy_re.search(name_re):
            details = 'Its name should begin with ' + name_re[1:]
        else:
            details = 'Its name should match the regular expression ' + name_re

        self.output.error_details.update({pkg_name + '-naming-policy-not-applied':
                                         """This package doesn't respect the naming policy for %s
                                         packages.\n%s.""" % (pkg_name, details)})

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
            self.output.add_info('W', pkg, c['pkg_name'] + '-naming-policy-not-applied', f)
