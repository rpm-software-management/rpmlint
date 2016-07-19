#!/bin/sh

export PYTHONPATH=$(pwd)/tools:$(pwd)
export TESTPATH="$(pwd)/test/"
: ${PYTHON:=python} ${PYTEST:=py.test} ${FLAKE8:=flake8}
: ${PYTHONWARNINGS:=all}
export PYTHONWARNINGS

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
echo "...in default locale"
$PYTHON ./rpmlint -C $(pwd) test/*/*.rpm test/spec/*.spec >/dev/null
rc=$?
test $rc -eq 0 -o $rc -eq 64 || exit $rc
echo "...in the C locale"
LC_ALL=C $PYTHON ./rpmlint -C $(pwd) test/*/*.rpm test/spec/*.spec >/dev/null
rc=$?
test $rc -eq 0 -o $rc -eq 64 || exit $rc

echo "$PYTEST tests"
$PYTEST -v || exit $?

unset PYTHONWARNINGS

echo "$FLAKE8 tests"
$FLAKE8 . ./rpmdiff ./rpmlint || exit $?

echo "man page tests"
if man --help 2>&1 | grep -q -- --warnings; then
    tmpfile=$(mktemp) || exit 1
    for manpage in ./rpmdiff.1 ./rpmlint.1; do
        man --warnings $manpage >/dev/null 2>$tmpfile
        if [ -s $tmpfile ]; then
            echo $manpage:
            cat $tmpfile
            rm -f $tmpfile
            exit 1
        else
            >$tmpfile
        fi
    done
    rm -f $tmpfile
else
    echo "Skipped, man does not seem to recognize the --warnings switch"
fi
