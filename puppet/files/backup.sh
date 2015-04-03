#!/usr/bin/env bash

set -e

tarcmd=(tar cf - --numeric-owner -C /)
common_findopts=(-type f -a -print0)
specialfiles=(
    boot
    lib/modules var/lib/dkms
    vmlinuz initrd.img
    etc/{blkid.,fs}tab)

all_pkgs() {
    dpkg-query -W -f '${Package}:${Architecture}\n'
}

declare -A SYSTEM_FILES

collect_systemfiles() {
    local all_pkgs=($(all_pkgs))

    while read -r; do
        if ! [[ -z "$REPLY" ]]; then
            SYSTEM_FILES[$REPLY]=1
        fi
    done < <(dpkg-query -L "${all_pkgs[@]}")
}

not_systemfile() {
    [[ -z "${SYSTEM_FILES[$1]}" ]]
}

find_systemfiles() {
    local excludes=(
        "${specialfiles[@]}"
        dev proc run sys tmp
        home place
        usr/share/{mime,snmp}
        var/{cache,log,local,spool,tmp}
        var/lib/{apt{,itude},dpkg}
        {data/,var/lib/}vz/{dump,lock,private,root}
        var/lib/{gems,nagios3/spool,puppet})
    local exts=(d o pyc)
    local cmd=(find /) start=1
    for path in "${excludes[@]}"; do
        [[ -z "$start" ]] && cmd+=(-o) || start=
        cmd+=(-path "/$path" -prune)
    done
    for ext in "${exts[@]}"; do cmd+=(-o -name "*.$ext"); done
    cmd+=(-o "${common_findopts[@]}")
    "${cmd[@]}"
}

find_userfiles() {
    find /home "${common_findopts[@]}"
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

    "${tarcmd[@]}" -T <(while read -r; do
        local sum="${REPLY%%  *}" file="${REPLY#*  }"
        if [[ "${conffiles[$file]}" != "$sum" ]]; then
            echo "${file:1}"
        fi
    done < <(md5sum "${!conffiles[@]}"))
}

find_specialfiles() {
    files=()
    for file in "${specialfiles[@]}"; do
        [[ -e "/$file" ]] && files+=("/$file")
    done
    find "${files[@]}" "${common_findopts[@]}"
}

diff_backup() {
    local findcmd=$1 filtercmd=$2

    declare -A md5sums
    while read -r -d ''; do
        md5sum=${REPLY%% *}
        file="/${REPLY#* }"
        md5sums[$file]=$md5sum
    done

    "${tarcmd[@]}" --null -T <(
        to_check=()
        while read -r -d ''; do
            if "$filtercmd" "$REPLY"; then
                if [[ -z "${md5sums[$REPLY]}" ]]; then
                    echo -en "${REPLY:1}\0"
                else
                    to_check+=("$REPLY")
                fi
            fi
        done < <("$findcmd")

        if [[ "${#to_check[@]}" -gt 0 ]]; then
            for file in "${to_check[@]}"; do
                echo -en "$file\0"
            done | xargs --null md5sum | while read -r; do
                start=${REPLY:0:1}
                filename=${REPLY#*  }
                if [[ "$start" == '\' ]]; then
                    filename=$(echo -en "$filename")
                    sum=${REPLY:1:32}
                else
                    sum=${REPLY:0:32}
                fi
                if [[ "${md5sums[$filename]}" != "$sum" ]]; then
                    echo -en "${filename:1}\0"
                fi
            done
        fi
    )
}

backup_mysql() {
    mysqldump \
        --defaults-extra-file=/etc/mysql/debian.cnf \
        --lock-tables \
        --all-databases \
        --events --ignore-table=mysql.event \
        --default-character-set=utf8 | \
    gzip
}

case "$1" in
    pkgs)       apt-mark showmanual ;;
    conf)       conffiles ;;
    sys)        collect_systemfiles; diff_backup find_systemfiles not_systemfile ;;
    user)       diff_backup find_userfiles true ;;
    special)    diff_backup find_specialfiles true ;;
    mysql)      backup_mysql ;;
    postgresql) su postgres -c 'pg_dumpall | gzip' ;;
    *)          exit 1 ;;
esac
