#!/usr/bin/env bash

set -e

if [[ "$#" -lt 2 ]]; then
    echo "usage: $0 <host> {full,diff} <data> [data...]" 1>&2
    exit 1
fi

host=$1; shift

backup="/usr/local/bin/backup.sh"
remote=(ssh "$host" -l root "$backup")

ppattern=%F_%H-%M-%S
spattern=????-??-??_??-??-??
fullprefix=full

generate_timestamp() {
    date "+$ppattern"
}

last_fullname() {
    local src=$1
    shopt -s nullglob
    local names=($src/${fullprefix}_${spattern})
    if [[ "${#names[@]}" -gt 0 ]]; then
        echo "${names[-1]}"
    fi
}

backup_pkgs() {
    "${remote[@]}" pkgs > "$1"
}

backup_conffiles() {
    "${remote[@]}" conf > "$1"
}

backup_sysfiles() {
    local sumfile=$1 output=$2
    "$backup" remote_backup "root@$host" sys "$sumfile" "$output"
    "$backup" update "$sumfile" "$output"
}

full_backup() {
    local stamp=$(generate_timestamp)
    local dest="$HOME/${fullprefix}_${stamp}"
    if [[ -r "$dest" ]]; then
        echo "$dest already exists, refusing to overwrite." >&2
        exit 1
    fi

    mkdir -p "$dest"
    chmod 700 "$dest"

    backup_pkgs "$dest/pkgs_$stamp"
    backup_conffiles "$dest/conffiles_$stamp.tar"

    for type in "$@"; do
        case "$type" in
            sys) backup_sysfiles "$dest/sysfiles.md5sums" \
                                 "$dest/sysfiles_${stamp}.tar" ;;
            *)   echo "unknown type: $type" 1>&2; exit 1 ;;
        esac
    done
}

diff_backup() {
    local last_full=$(last_fullname "$HOME")
    if [[ -z "$last_full" ]] || ! [[ -d "$last_full" ]]; then
        echo 'No full backup exists, creating one now.' >&2
        full_backup "$@"
    else
        local stamp=$(generate_timestamp)

        backup_pkgs "$last_full/pkgs_$stamp"
        backup_conffiles "$last_full/conffiles_$stamp.tar"

        for type in "$@"; do
            case "$type" in
                sys) backup_sysfiles "$last_full/sysfiles.md5sums" \
                                     "$last_full/sysfiles_${stamp}.tar" ;;
                *)   echo "unknown type: $type" 1>&2; exit 1 ;;
            esac
        done
    fi
}

clean_older_than() {
    local last_full=$(last_fullname "$HOME")
    if [[ -z "$last_full" ]]; then
        echo "No full backup detected" >&2
        return
    fi
    local goal="$HOME/${fullprefix}_$(python -c 'import datetime, sys
def get_param(param):
    name, value = param.split("=")
    return name, int(value)
params = dict(map(get_param, sys.argv[1:]))
delta = datetime.timedelta(**params)
goal = datetime.datetime.now() - delta
print goal.strftime("%Y-%m-%d_%H-%M-%S")' "$@")"
    shopt -s nullglob
    for name in $HOME/${fullprefix}_$spattern; do
        if [[ "$name" < "$goal" ]] && [[ "$name" != "$last_full" ]]; then
            rm -rf "$name"
        fi
    done
}

btype=$1
shift

case "$btype" in
    full)  full_backup "$@" ;;
    diff)  diff_backup "$@" ;;
    clean) clean_older_than "$@" ;;
    *)    echo "unknown backup type: $btype" 1>&2; exit 1 ;;
esac
