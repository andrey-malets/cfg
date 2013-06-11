#!/bin/bash -xe

BASE=`dirname $0`
MAIN="python ./main.py"
SERIAL="python ./util/serial.py"
DATA=/var/lib/cfg

export CFG=$BASE/cfg/conf.yaml

gen_dhcp() {
    local CUR=/etc/dhcp/dhcpd.conf
    local NEW=$DATA/dhcpd.conf

    $MAIN dhcp $BASE/cfg/dhcp.template > $NEW

    set +e; cmp -s $CUR $NEW; rv=$?; set -e

    if [ $rv -ne 0 ]; then
        mv $NEW $CUR
        /etc/init.d/isc-dhcp-server restart
    else
        rm $NEW
    fi
}

gen_dns() {
    local ZONES="urgu.org"
    local RESTART=0
    
    for ZONE in $ZONES; do
        SFILE=$DATA/$ZONE.serial
        set +e; SOLD=$($SERIAL get $SFILE 2>/dev/null); rv=$?; set -e
        if [ $rv -ne 0 ]; then
            RESTART=1
            local SNEW=$($SERIAL inc $SFILE)
            $MAIN dns cfg/$ZONE.template $SNEW $ZONE > $DATA/$ZONE.master
        else
            $MAIN dns cfg/$ZONE.template $SOLD $ZONE > $DATA/$ZONE.master.old
            set +e; cmp -s $DATA/$ZONE.master $DATA/$ZONE.master.old; rv=$?; set -e
            if [ $rv -ne 0 ]; then
                rm $DATA/$ZONE.master.old
                SNEW=$($SERIAL inc $SFILE)
                $MAIN dns cfg/$ZONE.template $SNEW $ZONE > $DATA/$ZONE.master.new
                mv $DATA/$ZONE.master.new $DATA/$ZONE.master
            else
                rm $DATA/$ZONE.master.old
            fi
        fi
    done
}

mkdir -p $DATA

gen_dhcp
gen_dns
