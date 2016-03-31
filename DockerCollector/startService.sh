#!/bin/sh
if [ "$1" = "" ]; 
then   
    workroot=`pwd`
else
    workroot=$1
    cd $workroot
fi
export PYTHONPATH="."
PROCESS_NUM=`ps -ef | grep "python $workroot/ServerMain" | grep -v "grep" | wc -l`
if [ $PROCESS_NUM -gt 0 ]; 
then   
    echo "the Service is already running!"
    exit 1
else   
    if [ -f "$workroot/ServerMain.pyc" ]; then
        nohup python $workroot/ServerMain.pyc >$workroot/main.out &
    else
        nohup python $workroot/ServerMain.py >$workroot/main.out &
    fi
    echo "--------------started---------------"

fi
