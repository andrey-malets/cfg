#!/bin/bash

attr=${1?no attribute specified}

res=($(ip route | grep "$attr" | while read route ; do
    tokens=($route)
    dst=${tokens[0]}
    for i in $(seq 1 2 ${#tokens[*]}); do
        if [ "${tokens[i]}" = "$attr" ]; then
            echo $dst:${tokens[i+1]}
        fi
    done
done))

IFS=,; echo "${res[*]}"
