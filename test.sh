export PYTHONPATH=$(pwd)
export TESTPATH="$(pwd)/test/"

for i in $TESTPATH/test.*.py; do
    python $i
    RET=$? 
    if [ $RET -ne 0 ]; then
        exit $RET
    fi;
done;

echo "Check if rpmlint have no errors"
python ./rpmlint.py -C $(pwd) test/*rpm >/dev/null 
