from Testing import get_tested_mock_package


SCRIPT1 = """#!/bin/sh
xz $tmp/1 &> /dev/null
"""

SCRIPT2 = """#!/bin/sh
do
"""


BashismsPackage = get_tested_mock_package(
    files={
        '/bin/script1': {'content': SCRIPT1},
        '/bin/script2': {'content': SCRIPT2},
    },
)
