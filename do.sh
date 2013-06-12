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
    local RELOAD=0 RESTART=0
    
    for ZONE in $ZONES; do
        SFILE=$DATA/$ZONE.serial
        set +e; SOLD=$($SERIAL get $SFILE 2>/dev/null); rv=$?; set -e
        if [ $rv -ne 0 ]; then
            RELOAD=1
            local SNEW=$($SERIAL inc $SFILE)
            $MAIN dns cfg/$ZONE.template $SNEW $ZONE > $DATA/$ZONE.master
        else
            $MAIN dns cfg/$ZONE.template $SOLD $ZONE > $DATA/$ZONE.master.old
            set +e; cmp -s $DATA/$ZONE.master $DATA/$ZONE.master.old; rv=$?; set -e
            if [ $rv -ne 0 ]; then
                RELOAD=1
                rm $DATA/$ZONE.master.old
                SNEW=$($SERIAL inc $SFILE)
                $MAIN dns cfg/$ZONE.template $SNEW $ZONE > $DATA/$ZONE.master.new
                mv $DATA/$ZONE.master.new $DATA/$ZONE.master
            else
                rm $DATA/$ZONE.master.old
            fi
        fi
    done

    for NET in $($MAIN rdns_nets); do
        SFILE=$DATA/$NET.serial
        set +e; SOLD=$($SERIAL get $SFILE 2>/dev/null); rv=$?; set -e
        if [ $rv -ne 0 ]; then
            RELOAD=1
            local SNEW=$($SERIAL inc $SFILE)
            $MAIN rdns cfg/reverse.template $SNEW $NET > $DATA/$NET.master
        else
            $MAIN rdns cfg/reverse.template $SOLD $NET > $DATA/$NET.master.old
            set +e; cmp -s $DATA/$NET.master $DATA/$NET.master.old; rv=$?; set -e
            if [ $rv -ne 0 ]; then
                RELOAD=1
                rm $DATA/$NET.master.old
                SNEW=$($SERIAL inc $SFILE)
                $MAIN rdns cfg/reverse.template $SNEW $NET > $DATA/$NET.master.new
                mv $DATA/$NET.master.new $DATA/$NET.master
            else
                rm $DATA/$NET.master.old
            fi
        fi
    done

    local CUR=$DATA/reverse.config
    local NEW=$DATA/reverse.config.new
    
    $MAIN rdns_cfg cfg/rdns_cfg.template $DATA/%s.master /etc/bind/db.empty > $NEW

    set +e; cmp -s $CUR $NEW; rv=$?; set -e

    if [ $rv -ne 0 ]; then
        mv $NEW $CUR
        RESTART=1
    else
        rm $NEW
    fi

    if [ $RESTART -ne 0 ]; then
        /etc/init.d/bind9 restart
    elif [ $RELOAD -ne 0 ]; then
        /etc/init.d/bind9 reload
    fi
}

mkdir -p $DATA

gen_dhcp
gen_dns
