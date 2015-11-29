from FilesCheck import python_bytecode_to_script as pbts


class TestPythonBytecodeToScript(object):

    def test_pep3147(self):
        assert pbts("/usr/lib64/python3.4/__pycache__/__phello__.foo.cpython-34.pyc") == "/usr/lib64/python3.4/__phello__.foo.py"
        assert pbts("/usr/lib64/python3.4/__pycache__/__phello__.foo.cpython-34.pyo") == "/usr/lib64/python3.4/__phello__.foo.py"

    def test_py2(self):
        assert pbts("/usr/lib/python2.7/site-packages/_pytest/main.pyc") == "/usr/lib/python2.7/site-packages/_pytest/main.py"
        assert pbts("/usr/lib/python2.7/site-packages/_pytest/main.pyo") == "/usr/lib/python2.7/site-packages/_pytest/main.py"

    def test_pep0488(self):
        assert pbts("/usr/lib/python3.5/site-packages/__pycache__/pytest.cpython-35.opt-1.pyc") == "/usr/lib/python3.5/site-packages/pytest.py"
        assert pbts("/usr/lib/python3.5/site-packages/__pycache__/pytest.cpython-35.opt-2.pyc") == "/usr/lib/python3.5/site-packages/pytest.py"
        assert pbts("/usr/lib/python3.5/site-packages/__pycache__/pytest.cpython-35.pyc") == "/usr/lib/python3.5/site-packages/pytest.py"

# ex: ts=4 sw=4 et
