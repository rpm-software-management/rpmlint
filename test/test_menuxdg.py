import os

import MenuXDGCheck
import Testing


class TestMenuXDGParsing(Testing.OutputTest):

    @classmethod
    def setup_class(cls):
        cls.check = MenuXDGCheck.check.check

    def test_raises_parse_error(self):
        for package in ['menuxdg1']:
            out = self._rpm_test_output(os.path.join('binary', package))
            assert 'contains parsing error' in "\n".join(out)
            assert ' invalid-desktopfile ' in "\n".join(out)
