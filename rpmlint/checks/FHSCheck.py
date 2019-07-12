#############################################################################
# File          : FHSCheck.py
# Package       : rpmlint
# Author        : Frederic Lepied
# Created on    : Fri Oct 15 17:40:32 1999
# Purpose       : check FHS conformity
#############################################################################

import re

from rpmlint.checks.AbstractCheck import AbstractCheck


class FHSCheck(AbstractCheck):
    usr_regex = re.compile('^/usr/([^/]+)/')
    usr_subdir = ('X11R6', 'bin', 'games', 'include', 'lib', 'lib64',
                  'local', 'sbin', 'share', 'src', 'tmp')
    var_regex = re.compile('^/var/([^/]+)/')
    var_fsstnd = ('adm', 'catman', 'local', 'named', 'nis', 'preserve')
    var_subdir = ('account', 'cache', 'crash', 'games', 'lib', 'lock', 'log',
                  'mail', 'opt', 'run', 'spool', 'tmp', 'yp', 'www', 'ftp')

    def __init__(self, config, output):
        super().__init__(config, output)
        self.output.error_details.update(fhs_details_dict)

    def check_binary(self, pkg):
        var_list = []
        usr_list = []

        for fname in pkg.files():
            s = FHSCheck.usr_regex.search(fname)
            if s:
                d = s.group(1)
                if d not in FHSCheck.usr_subdir and d not in usr_list:
                    self.output.add_info('W', pkg, 'non-standard-dir-in-usr', d)
                    usr_list.append(d)
            else:
                s = FHSCheck.var_regex.search(fname)
                if s:
                    d = s.group(1)
                    if d in var_list:
                        continue
                    if d in FHSCheck.var_fsstnd:
                        self.output.add_info('W', pkg, 'FSSTND-dir-in-var', fname)
                        var_list.append(d)
                    elif d not in FHSCheck.var_subdir:
                        self.output.add_info('W', pkg, 'non-standard-dir-in-var', d)
                        var_list.append(d)


fhs_details_dict = {
'non-standard-dir-in-usr':
"""Your package is creating a non-standard subdirectory in /usr. The standard
directories are:
%s.""" % ', '.join(FHSCheck.usr_subdir),

'FSSTND-dir-in-var':
"""Your package is creating an illegal directory in /var. The FSSTND (illegal)
ones are:
%s.""" % ', '.join(FHSCheck.var_fsstnd),

'non-standard-dir-in-var':
"""Your package is creating a non-standard subdirectory in /var. The standard
directories are:
%s.""" % ', '.join(FHSCheck.var_subdir),
}
