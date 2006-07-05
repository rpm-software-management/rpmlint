export PYTHONPATH=$(pwd)
export TESTPATH="$(pwd)/test/"
for i in $TESTPATH/test.*.py; do
    echo $i
    python $i
    #if [ -n $? ]; then
    #    exit $?
    #fi;
done;
