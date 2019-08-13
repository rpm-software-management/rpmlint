import re


class AbstractCheck(object):
    def __init__(self, config, output):
        # Note: do not add any capturing parentheses here
        self.macro_regex = re.compile(r'%+[{(]?[a-zA-Z_]\w{2,}[)}]?')
        self.config = config
        self.output = output

    def check(self, pkg):
        if pkg.isSource():
            return self.check_source(pkg)
        return self.check_binary(pkg)

    def check_source(self, pkg):
        return

    def check_binary(self, pkg):
        return

    def check_spec(self, pkg):
        return


class AbstractFilesCheck(AbstractCheck):
    def __init__(self, config, output, file_regexp):
        self.__files_re = re.compile(file_regexp)
        super().__init__(config, output)

    def check_binary(self, pkg):
        ghosts = pkg.ghostFiles()
        for filename in (x for x in pkg.files() if x not in ghosts):
            if self.__files_re.match(filename):
                self.check_file(pkg, filename)

    def check_file(self, pkg, filename):
        """Virtual method called for each file that match the regexp passed
        to the constructor.
        """
        raise NotImplementedError('check must be implemented in subclass')
