import os

import SourceCheck
import Testing


class TestSourceCheck(Testing.OutputTest):

    @classmethod
    def setup_class(cls):
        cls.check = SourceCheck.check.check

    def test_inconsistent_file_extension(self):
        for package in ['wrongsrc']:
            out = self._rpm_test_output(os.path.join('source', package))
            assert 'inconsistent-file-extension' in "\n".join(out)
