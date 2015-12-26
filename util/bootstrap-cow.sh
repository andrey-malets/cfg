#!/usr/bin/env bash

set -e

get_property() {
    local url=https://urgu.org/config
    local name=$1 query=$2 sel=$3
    curl "$url/$name?$query" | jq "$sel"
}

ssh_opts=(-q -o StrictHostKeyChecking=no
          -o GlobalKnownHostsFile=/dev/null -o UserKnownHostsFile=/dev/null)

do_ssh() { ssh "${ssh_opts[@]}" "$@"; }

name=${1:?no hostname specified}
partition="/dev/disk/by-partlabel/${2:-cow-image64-keyimage}"

host=$(get_property "$name" "" ".name" | cut -f2 -d\")
image="/var/lib/cfg/keys_images/$host"

if ! [[ -f "$image" ]]; then
    echo "no keyimage for $host, please run do.sh gen_keys_images" >&2
    exit 1
fi

do_ssh "$host" "disk.py"
cat "$image" | do_ssh "$host" "dd of=$partition"
do_ssh "$host" "reboot"
