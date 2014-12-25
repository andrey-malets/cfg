#!/usr/bin/env bash

set -e

pwds="$(dirname "$0")/../cfg/pwds"

shit() {
    echo "$@" 1>&2
    exit 1
}

if [[ "$#" -lt 2 ]]; then shit "Usage: $0 <host> <cmd> [args..]"; fi

host="$1"
shift

spec=$(grep "$host::" "$pwds" | cut -f3 -d:)
if [[ -z "$spec" ]]; then shit "no pwd for $host"; fi

export IPMI_PASSWORD="${spec#*,}"
case "${spec%%,*}" in
    1) ipmitool -I lanplus -o intelplus -H "$host" -E -e @ $@ ;;
    2) ipmitool -I lanplus -U root -H "$host" -E -e @ $@ ;;
    *) shit "unknown proto: ${spec%%,*}" ;;
esac
