#!/usr/bin/env bash

set -e

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

update() {
    local sumfile=$1 backup=$2

    declare -A md5sums
    while read -r -d ''; do
        md5sum=${REPLY%% *}
        file=${REPLY#* }
        md5sums[$file]=$md5sum
    done < "$sumfile"

    script='
import md5, sys, tarfile

with tarfile.open(sys.argv[1]) as tfile:
    for member in tfile:
        md5sum = md5.new()
        memberfile = tfile.extractfile(member)
        while True:
            data = memberfile.read(4096)
            if len(data) == 0:
                break
            md5sum.update(data)
        sys.stdout.write("{} {}\0".format(md5sum.hexdigest(),
                                          member.name))'
    while read -r -d ''; do
        md5sum=${REPLY%% *}
        file=${REPLY#* }
        md5sums[$file]=$md5sum
    done < <(python -c "$script" "$backup")

    for file in "${!md5sums[@]}"; do
        echo -en "${md5sums[$file]} $file\0"
    done > "$sumfile.new"

    mv "$sumfile.new" "$sumfile"
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

remote_backup() {
    local host=$1; shift
    local backup_cmd="/usr/local/bin/backup.sh"
    ssh -l root "$host" "$backup_cmd" "$@"
}

get_destination() {
    local stamp=$1
    echo "$HOME/${fullprefix}_${stamp}"
}

get_name() {
    local type=$1 dest=$2 stamp=$3
    case "$type" in
        pkgs) fn="pkgs_$stamp" ;;
        conf) fn="conffiles_$stamp.tar" ;;
        sys)  fn="sysfiles_$stamp.tar" ;;
        user) fn="userfiles_$stamp.tar" ;;
        *)    echo "unknown type: $type" >&2; exit 1 ;;
    esac
    echo "$dest/$fn"
}

get_sumname() {
    local type=$1 dest=$2
    case "$type" in
        sys)  fn=sysfiles ;;
        user) fn=userfiles ;;
        *)    echo "unknown type: $type" >&2; exit 1 ;;
    esac
    echo "$dest/$fn.md5sums"
}

backup_smallfiles() {
    local host=$1 dest=$2 stamp=$3
    for type in pkgs conf; do
        remote_backup "$host" "$type" > "$(get_name "$type" "$dest" "$stamp")"
    done
}

backup_with_sums() {
    local host=$1 cmd=$2 sumfile=$3 output=$4
    touch "$sumfile"
    remote_backup "$host" "$cmd" < "$sumfile" > "$output"
    update "$sumfile" "$output"
}

backup_bigfiles() {
    local host=$1 dest=$2 stamp=$3; shift 3
    for type in "$@"; do
        case "$type" in
            sys|user) backup_with_sums "$host" "$type" \
                                       "$(get_sumname "$type" "$dest")" \
                                       "$(get_name "$type" "$dest" "$stamp")" ;;
            *)        echo "unknown type: $type" 1>&2; exit 1 ;;
        esac
    done
}

full_backup() {
    local host=$1 stamp=$(generate_timestamp)
    local dest=$(get_destination "$stamp")
    shift

    if [[ -r "$dest" ]]; then
        echo "$dest already exists, refusing to overwrite." >&2
        exit 1
    fi

    mkdir -p -m 700 "$dest"
    backup_smallfiles "$host" "$dest" "$stamp"
    backup_bigfiles "$host" "$dest" "$stamp" "$@"
}

diff_backup() {
    local host=$1 last_full=$(last_fullname "$HOME")
    shift
    if [[ -z "$last_full" ]] || ! [[ -d "$last_full" ]]; then
        echo 'No full backup exists, creating one now.' >&2
        full_backup "$@"
    else
        local stamp=$(generate_timestamp)
        backup_smallfiles "$host" "$last_full" "$stamp"
        backup_bigfiles "$host" "$last_full" "$stamp" "$@"
    fi
}

if [[ "$#" -lt 2 ]]; then
    echo "usage: $0 <host> {full,diff} <data> [data...]" 1>&2
    exit 1
fi

host=$1; btype=$2; shift 2
case "$btype" in
    full)  full_backup "$host" "$@" ;;
    diff)  diff_backup "$host" "$@" ;;
    clean) clean_older_than "$@" ;;
    *)     echo "unknown backup type: $btype" 1>&2; exit 1 ;;
esac
