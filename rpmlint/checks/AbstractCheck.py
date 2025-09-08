import concurrent.futures
import re


class AbstractCheck:
    def __init__(self, config, output):
        # Note: do not add any capturing parentheses here
        self.macro_regex = re.compile(r'%+[{(]?[a-zA-Z_]\w{2,}[)}]?')
        self.config = config
        self.output = output
        # by default do not track checked files
        self.checked_files = None

    def check(self, pkg):
        if pkg.is_source:
            return self.check_source(pkg)
        return self.check_binary(pkg)

    def check_source(self, pkg):
        return

    def check_binary(self, pkg):
        return

    def check_spec(self, pkg):
        return

    def after_checks(self):
        return

    def reset(self):
        return


class AbstractFilesCheck(AbstractCheck):
    def __init__(self, config, output, file_regexp):
        self.__files_re = re.compile(file_regexp)
        self.use_threads = False
        super().__init__(config, output)

    def check_binary(self, pkg):
        if self.checked_files is None:
            self.checked_files = 0

        filenames = [x for x in pkg.files if x not in pkg.ghost_files and self.__files_re.match(x)]
        if self.use_threads:
            # NOTE: the speed benefit of the ThreadPoolExecutor is limited due to
            # Global Interpreter Lock (GIL).

            # start with the biggest files first
            filenames = sorted(filenames, key=lambda x: pkg.files[x].size, reverse=True)
            with concurrent.futures.ThreadPoolExecutor() as executor:
                futures = [executor.submit(self.check_file, pkg, filename) for filename in filenames]
                concurrent.futures.wait(futures)
                for future in futures:
                    err = future.exception()
                    if err:
                        raise err
        else:
            for filename in filenames:
                self.check_file(pkg, filename)
        self.checked_files += len(filenames)

    def reset(self):
        self.checked_files = None

    def check_file(self, pkg, filename):
        """Virtual method called for each file that match the regexp passed
        to the constructor.
        """
        raise NotImplementedError('check must be implemented in subclass')
