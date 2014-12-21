#!/usr/bin/env bash

set -e

exec_findcmd() {
    local paths=(boot
                 lib/modules vmlinuz initrd.img
                 etc/{blkid.,fs}tab
                 dev proc run sys tmp
                 home place root
                 usr/share/{mime,snmp}
                 var/{cache,log,local,spool,tmp}
                 var/lib/{apt{,itude},dkms,dpkg,gems,nagios3/spool,puppet})
    local exts=(d o pyc)
    local cmd=(find /) start=1
    for path in "${paths[@]}"; do
        [[ -z "$start" ]] && cmd+=(-o) || start=
        cmd+=(-path "/$path" -prune)
    done
    for ext in "${exts[@]}"; do cmd+=(-o -name "*.$ext"); done
    cmd+=(-o -type f -a -print0)
    "${cmd[@]}"
}

manual_pkgs() {
    apt-mark showmanual
}

all_pkgs() {
    dpkg-query -W -f '${Package}:${Architecture}\n'
}

conffiles() {
    all_pkgs=($(all_pkgs))
    declare -A conffiles
    while read -r; do
        if ! [[ -z "$REPLY" ]]; then
            spec="${REPLY# *}"
            file="${spec% *}"
            sum="${spec##* }"
            if [[ -r "$file" ]]; then
                conffiles[$file]=$sum
            fi
        fi
    done < <(dpkg-query -f '${Conffiles}\n' -W "${all_pkgs[@]}")

    tar cf - -T <(while read -r; do
        local sum="${REPLY%%  *}" file="${REPLY#*  }"
        if [[ "${conffiles[$file]}" != "$sum" ]]; then
            echo "$file"
        fi
    done < <(md5sum "${!conffiles[@]}"))
}

systemfiles() {
    all_pkgs=($(all_pkgs))
    declare -A allfiles

    while read -r; do
        if ! [[ -z "$REPLY" ]]; then
            allfiles[$REPLY]=1
        fi
    done < <(dpkg-query -L "${all_pkgs[@]}")

    declare -A md5sums
    while read -r -d ''; do
        md5sum=${REPLY%% *}
        file="/${REPLY#* }"
        md5sums[$file]=$md5sum
    done

    tar cf - --null -T <(while read -r -d ''; do
        if [[ -z "${allfiles[$REPLY]}" ]]; then
            if [[ -z "${md5sums[$REPLY]}" ]] || \
               [[ "${md5sums[$REPLY]}" != \
                    "$(md5sum "$REPLY" | awk '{print $1}')" ]]; then
                echo -en "$REPLY\0"
            fi
        fi
    done < <(exec_findcmd))
}

userfiles() {
    tar cf - /home /root
}

remote_backup() {
    local rhost=$1 rcmd=$2 sumfile=$3 output=$4
    [[ -f "$sumfile" ]] || touch "$sumfile"
    ssh "$rhost" "/root/cfg_backup.sh" "$rcmd" < "$sumfile" > "$output"
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

case "$1" in
    pkgs) manual_pkgs ;;
    conf) conffiles ;;
    sys)  systemfiles ;;
    user) userfiles ;;

    remote_backup) shift; remote_backup "$@" ;;
    update)        shift; update "$@" ;;

    *)    exit 1 ;;
esac
