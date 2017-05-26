#!/bin/sh -ex

: ${PYTHON:=python}
export PYTHON

: ${PYTHONWARNINGS:=all}
export PYTHONWARNINGS

make check PYTHON=$PYTHON

make install PYTHON=$PYTHON DESTDIR=$(mktemp -d)
