from pathlib import Path
import re
import stat

from rpmlint.checks.AbstractCheck import AbstractFilesCheck
from rpmlint.checks.FilesCheck import FilesCheck
from rpmlint.checks.FilesCheck import script_interpreter


# Only allow "#!/usr/bin/ruby.ruby4.0" shebang format
# "/usr/bin/env ruby" or "/usr/bin/ruby" will show the
# ruby-script-wrong-shebang error
RUBY_SHEBANG_RE = re.compile(r'^/usr/bin/ruby\.(?P<suffix>.*)$')
BIN_RE = re.compile(r'^/(?:usr/(?:s?bin|games)|s?bin)/(.*)')


class RubyCheck(AbstractFilesCheck):
    man_regex = re.compile(r'/man(?:\d[px]?|n)/')
    info_regex = re.compile(r'(/usr/share|/usr)/info/')

    def __init__(self, config, output):
        super().__init__(config, output, r'.*')

    def check_file(self, pkg, filename):
        self._check_file_shebang(pkg, filename)

    def _check_file_shebang(self, pkg, filename):
        """
        Check that the file shebang is correct
        """

        if not BIN_RE.match(filename):
            return

        basedir = Path(filename).parent
        realbin = pkg.files[filename]
        if realbin.linkto:
            linkto = str((basedir / Path(realbin.linkto)).resolve())
            # Link to a file not in the package, so ignore
            if linkto not in pkg.files:
                return
            realbin = pkg.files[linkto]

        if not stat.S_ISREG(realbin.mode):
            return

        chunk, is_text = FilesCheck.peek(self, realbin.path, pkg)
        interpreter, interpreter_args = script_interpreter(chunk)
        if interpreter and RUBY_SHEBANG_RE.match(interpreter) is None:
            self.output.add_info('E', pkg, 'ruby-script-wrong-shebang', filename)
