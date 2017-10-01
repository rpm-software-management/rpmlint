import os

import TagsCheck
import Testing


class TestTags(Testing.OutputTest):

    @classmethod
    def setup_class(cls):
        cls.check = TagsCheck.check.check

    def test_unexpanded_macros(self):
        for package in ['unexpanded1']:
            out = self._rpm_test_output(os.path.join('binary', package))
            assert 'unexpanded-macro Recommends' in "\n".join(out)
            assert 'unexpanded-macro Provides' in "\n".join(out)
            assert 'unexpanded-macro Conflicts' in "\n".join(out)
            assert 'unexpanded-macro Suggests' in "\n".join(out)
            assert 'unexpanded-macro Obsoletes' in "\n".join(out)
            assert 'unexpanded-macro Enhances' in "\n".join(out)
