#!/usr/bin/env bash

set -e

exec_findcmd() {
    local paths=(boot
                 lib/modules vmlinuz initrd.img
                 dev proc run sys tmp
                 home root
                 usr/share/mime
                 var/{cache,log,local,spool}
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
    for spec in $(dpkg-query -f '${Conffiles}\n' -W "${all_pkgs[@]}" | \
                  egrep -v '^[[:space:]]*$' | awk '{print $1":"$2}'); do
        if [[ -r "${spec%%:*}" ]]; then
            conffiles[${spec%%:*}]=${spec##*:}
        fi
    done

    tar cf - -T <(md5sum "${!conffiles[@]}" | while read sum conffile; do
        if [[ "${conffiles[$conffile]}" != "$sum" ]]; then
            echo "$conffile"
        fi
    done)
}

systemfiles() {
    all_pkgs=($(all_pkgs))
    declare -A allfiles
    for file in $(dpkg-query -L "${all_pkgs[@]}" | \
                  egrep -v '^[[:space:]]*$'); do
        allfiles[$file]=1
    done

    tar cf - -T <(while read -r -d ''; do
        if [[ -z "${allfiles[$REPLY]}" ]]; then
            echo "$REPLY"
        fi
    done < <(exec_findcmd))
}

userfiles() {
    tar cf - /home /root
}

case "$1" in
    pkgs) manual_pkgs ;;
    conf) conffiles ;;
    sys)  systemfiles ;;
    user) userfiles ;;
    *)    exit 1 ;;
esac