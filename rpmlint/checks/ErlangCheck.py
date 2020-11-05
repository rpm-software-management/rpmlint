import re

from pybeam import BeamFile
from rpm import expandMacro
from rpmlint.checks.AbstractCheck import AbstractFilesCheck
from rpmlint.helpers import byte_to_string


class ErlangCheck(AbstractFilesCheck):
    def __init__(self, config, output):
        super().__init__(config, output, r'.*?\.beam$')
        build_dir = expandMacro('%_builddir')
        self.source_re = re.compile(build_dir)

    def check_file(self, pkg, filename):
        try:
            beam = BeamFile(pkg.files[filename].path)

            if beam.compileinfo is None:
                self.output.add_info('W', pkg, 'beam-compile-info-missed', filename)
                return

            compile_state = byte_to_string(str(beam.compileinfo['source']))
            if 'debug_info' not in beam.compileinfo['options']:
                self.output.add_info('E', pkg, 'beam-compiled-without-debuginfo', filename)

            # This can't be an error as builddir can be user specific and vary between users
            # it could be error in OBS where all the builds are done by user abuild, not in
            # general.
            if not self.source_re.match(compile_state):
                self.output.add_info('W', pkg, 'beam-was-not-recompiled', filename, compile_state)
        except Exception:
            self.output.add_info('E', pkg, 'pybeam-failed', filename)
