import re

from rpmlint.checks.AbstractCheck import AbstractCheck


class FHSCheck(AbstractCheck):
    """
    Validate that binary files are packaged according to FHS.

    We follow FHS 3.0 specification that can be found at
    http://refspecs.linuxfoundation.org/FHS_3.0/fhs-3.0.pdf

    FHS_usr_subdirs lists allowed directories in /usr (FHS chapter 4.2 and 4.3)
    FHS_var_subdirs lists allowed directories in /var (FHS chapter 5.2 and 5.3)
    """
    usr_regex = re.compile('^/usr/([^/]+)')
    FHS_usr_subdirs = ('bin', 'lib', 'local', 'sbin', 'share', 'games', 'include',
                       'libexec', 'lib64', 'src', 'spool', 'tmp')

    var_regex = re.compile('^/var/([^/]+)')
    FHS_var_subdirs = ('cache', 'lib', 'local', 'lock', 'log', 'opt', 'run',
                       'spool', 'tmp', 'account', 'crash', 'games', 'mail',
                       'yp')

    def __init__(self, config, output):
        super().__init__(config, output)
        self.output.error_details.update(fhs_details_dict)

    def check_binary(self, pkg):
        var_list = []
        usr_list = []

        for fname in pkg.files:
            usr_path = self.usr_regex.search(fname)
            if usr_path:
                # Run tests for /usr directory
                usr_file = usr_path.group(1)
                self._check_usr_standard_dir(usr_file, pkg, usr_list)
                continue

            var_path = self.var_regex.search(fname)
            if var_path:
                # Run tests for /var directory
                var_file = var_path.group(1)
                self._check_var_standard_dir(var_file, pkg, var_list)

    def _check_usr_standard_dir(self, usr_file, pkg, usr_list):
        """
        Check if the file is in valid subdirectory of /usr.

        FHS 3.0 says: "Large software packages must not use a direct
        subdirectory under the /usr hierarchy." Check if this package contains
        a directory in /usr that is not mentioned in FHS (FHS_usr_subdirs).

        Refer to http://refspecs.linuxfoundation.org/FHS_3.0/fhs/ch04.html for
        details.
        """
        if usr_file not in self.FHS_usr_subdirs and usr_file not in usr_list:
            usr_list.append(usr_file)
            self.output.add_info('W', pkg, 'non-standard-dir-in-usr', usr_file)

    def _check_var_standard_dir(self, var_file, pkg, var_list):
        """
        Check if the file is in valid subdirectory of /var.

        FHS 3.0 says: "Applications must generally not add directories to the
        top level of /var. Such directories should only be added if they have
        some system-wide implication, and in consultation with the FHS
        mailing list."

        Refer to http://refspecs.linuxfoundation.org/FHS_3.0/fhs/ch05.htm
        for details.
        """
        if var_file not in self.FHS_var_subdirs and var_file not in var_list:
            var_list.append(var_file)
            self.output.add_info('W', pkg, 'non-standard-dir-in-var', var_file)


fhs_details_dict = {
'non-standard-dir-in-usr':
"""Your package is creating a non-standard subdirectory in /usr. The standard
directories are:
%s.""" % ', '.join(FHSCheck.FHS_usr_subdirs),

'non-standard-dir-in-var':
"""Your package is creating a non-standard subdirectory in /var. The standard
directories are:
%s.""" % ', '.join(FHSCheck.FHS_var_subdirs),
}
