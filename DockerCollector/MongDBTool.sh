#! /bin/bash

export PYTHONPATH=`pwd`

if [[ "$1" = "" || "$1" = "-h" ]];
then
    python mongodb/dbtool.py -h 2>&1
else
    python mongodb/dbtool.py -l $1 $2 2>&1
fi
