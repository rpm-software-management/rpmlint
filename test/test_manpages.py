from shlex import split
from subprocess import PIPE, Popen

import pytest


@pytest.mark.parametrize('manpage', ['man/rpmlint.1', 'man/rpmdiff.1'])
def test_start(manpage):
    args = split('/usr/bin/man --warnings ' + manpage)
    process = Popen(args, stdout=PIPE, stderr=PIPE, shell=False)
    out, err = process.communicate()
    assert not err
