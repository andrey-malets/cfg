#!/bin/bash

if [ $# -ne 1 ]; then
    echo "usage: $0 <hostname>"
else
    BASE=$(dirname $0)
    export ROUTER_DEV=$($BASE/router-attrs.sh dev)
    cmdline=$(python $BASE/../main.py etherwake $1 < $BASE/../cfg/conf.yaml)
    rv=$?
    [ $rv -eq 0 ] && $cmdline
    exit $rv
fi
