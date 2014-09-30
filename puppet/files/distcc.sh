#!/bin/bash

export FILE=/etc/distcc/hosts

( set -o pipefail;
 /usr/bin/sinfo -p managed -t idle -h -o '%c %n' 2>/dev/null |\
 sort -r |\
 while read cpus host; do
    for i in $(seq $((cpus*2))); do
        echo $host #,cpp,lzo
    done
 done > $FILE.new && mv $FILE.new $FILE
) || exit 0
