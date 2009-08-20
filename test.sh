#!/bin/sh

export PYTHONPATH=$(pwd)/tools:$(pwd)
export TESTPATH="$(pwd)/test/"

for i in $TESTPATH/test.*.py; do
    python $i
    RET=$? 
    if [ $RET -ne 0 ]; then
        exit $RET
    fi
done

echo "Check that rpmlint executes with no unexpected errors"
python ./rpmlint.py -C $(pwd) test/*.rpm test/*.spec >/dev/null
rc=$?
test $rc -eq 0 -o $rc -eq 64
