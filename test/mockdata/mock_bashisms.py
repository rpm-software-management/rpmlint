from Testing import get_tested_mock_package

BASHISMS = get_tested_mock_package(
    files={
        '/bin/script1': {'content': """#!/bin/sh
xz $tmp/1 &> /dev/null
"""},
        '/bin/script2': {'content': """#!/bin/sh
do
"""}
    })
