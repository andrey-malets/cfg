#!/usr/bin/env bash

set -e

if [[ "$#" -lt 2 ]]; then
    echo "usage: $0 <host> <type> [type...]" 1>&2
    exit 1
fi

host=$1
shift

backup="/usr/local/bin/backup.sh"
remote=(ssh "$host" -l root "$backup")

basedir="$HOME/$(date +%F)"
stamp=$(date +%F_%H-%M-%S)

mkdir -p "$basedir"

for type in "$@"; do
    case "$type" in
        pkgs) "${remote[@]}" pkgs > "$basedir/pkgs_$stamp" ;;
        conf) "${remote[@]}" conf > "$basedir/conffiles_$stamp.tar" ;;
        sys)
            sumfile="$HOME/sys.md5sums"
            output="$basedir/sysfiles_$stamp.tar"
            "$backup" remote_backup "root@$host" sys "$sumfile" "$output"
            "$backup" update "$sumfile" "$output"
        ;;
        *)    echo "unknown type: $type" 1>&2 ;;
    esac
done
