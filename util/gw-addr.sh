#!/bin/bash

res=($(ip route | grep src | while read route ; do
    tokens=($route)
    dst=${tokens[0]}
    for i in $(seq 1 2 ${#tokens[*]}); do
        if [ "${tokens[i]}" = src ]; then
            echo $dst:${tokens[i+1]}
        fi
    done
done))

IFS=,; echo "${res[*]}"
