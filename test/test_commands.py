from shlex import split
from subprocess import PIPE, Popen
from sys import executable

import pytest


@pytest.mark.parametrize('script', ['lint.py', 'diff.py'])
def test_execution(script):
    args = split(executable + ' ./scripts/' + script)
    process = Popen(args, stdout=PIPE, stderr=PIPE, shell=False)
    out, err = process.communicate()
    assert not err
    assert '.py [<options>]' in out.decode("utf-8")


@pytest.mark.parametrize('arguments', ['test/*/*.rpm test/spec/*.spec', '- < $TESTPATH/spec/SpecCheck.spec'])
def test_arguments(arguments):
    args = split(executable + ' ./scripts/lint.py ' + arguments)
    process = Popen(args, stdout=PIPE, stderr=PIPE, shell=False)
    out, err = process.communicate()
    print(out)
    print(err)
    assert process.returncode == 0 or process.returncode == 64
