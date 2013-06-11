#!/bin/bash -x

BASE=`dirname $0`
MAIN="python ./main.py"
DATA=/var/lib/cfg

export CFG=$BASE/cfg/conf.yaml

gen_dhcp() {
    local CUR=/etc/dhcp/dhcpd.conf
    local NEW=$DATA/dhcpd.conf
    $MAIN dhcp $BASE/cfg/dhcp.template > $NEW
    local rv=$?
    if [ $rv -eq 0 ]; then
        cmp -s $CUR $NEW
        if [ $? -ne 0 ]; then
            mv $NEW $CUR
            /etc/init.d/isc-dhcp-server restart
        else
            rm $NEW
        fi
        exit $?
    else
        exit $rv
    fi
}

mkdir -p $DATA
gen_dhcp
