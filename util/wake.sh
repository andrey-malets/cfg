#!/bin/bash

if [ $# -ne 1 ]; then
    echo "usage: $0 <hostname>"
else
    BASE=`dirname $0`
    cmdline=`python $BASE/../main.py etherwake $1 < $BASE/../cfg/conf.yaml`
    rv=$?
    if [ $rv -eq 0 ]; then
        $cmdline
    fi
    exit $rv
fi
