#!/bin/sh

export PYTHONPATH=$(pwd)/tools:$(pwd)
export TESTPATH="$(pwd)/test/"
: ${PYTHON:=python} ${PYTEST:=py.test} ${FLAKE8:=flake8}

echo
echo "Please ignore the possibly occurring output like this:"
echo "    .../Patch*.patch: No such file or directory"
echo

for i in $TESTPATH/test.*.py; do
    $PYTHON $i
    RET=$?
    if [ $RET -ne 0 ]; then
        exit $RET
    fi
done

echo "Check that rpmlint executes with no unexpected errors"
$PYTHON ./rpmlint -C $(pwd) test/*/*.rpm test/spec/*.spec >/dev/null
rc=$?
test $rc -eq 0 -o $rc -eq 64 || exit $rc

echo "$PYTEST tests"
$PYTEST -v || exit $?

echo "$FLAKE8 tests"
$FLAKE8 . ./rpmdiff ./rpmlint || exit $?
