#!/bin/bash -e

BASE=`dirname $0`
MAIN="python $BASE/main.py"
SERIAL="python $BASE/util/serial.py"
DATA=/var/lib/cfg

CFGDIR=$BASE/cfg

export CFG=$CFGDIR/conf.yaml

gen_dhcp() {
    local CUR=/etc/dhcp/dhcpd.conf
    local NEW=$DATA/dhcpd.conf

    $MAIN dhcp $CFGDIR/dhcp.template > $NEW

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
            $MAIN dns $CFGDIR/$ZONE.template $SNEW $ZONE > $DATA/$ZONE.master
        else
            $MAIN dns $CFGDIR/$ZONE.template $SOLD $ZONE > $DATA/$ZONE.master.old
            set +e; cmp -s $DATA/$ZONE.master $DATA/$ZONE.master.old; rv=$?; set -e
            if [ $rv -ne 0 ]; then
                RELOAD=1
                rm $DATA/$ZONE.master.old
                SNEW=$($SERIAL inc $SFILE)
                $MAIN dns $CFGDIR/$ZONE.template $SNEW $ZONE > $DATA/$ZONE.master.new
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
            $MAIN rdns $CFGDIR/reverse.template $SNEW $NET > $DATA/$NET.master
        else
            $MAIN rdns $CFGDIR/reverse.template $SOLD $NET > $DATA/$NET.master.old
            set +e; cmp -s $DATA/$NET.master $DATA/$NET.master.old; rv=$?; set -e
            if [ $rv -ne 0 ]; then
                RELOAD=1
                rm $DATA/$NET.master.old
                SNEW=$($SERIAL inc $SFILE)
                $MAIN rdns $CFGDIR/reverse.template $SNEW $NET > $DATA/$NET.master.new
                mv $DATA/$NET.master.new $DATA/$NET.master
            else
                rm $DATA/$NET.master.old
            fi
        fi
    done

    local CUR=$DATA/reverse.config
    local NEW=$DATA/reverse.config.new
    
    $MAIN rdns_cfg $CFGDIR/rdns_cfg.template $DATA/%s.master /etc/bind/db.empty > $NEW

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

gen_puppet_cfg() {
    local DIR=$DATA/puppet
    mkdir -p $DIR

    local CUR=/etc/puppet/manifests/site.pp
    local NEW=$DIR/site.pp
    $MAIN puppet_cfg $CFGDIR/puppet_cfg.template > $NEW
    mv $NEW $CUR
}

gen_puppet_fileserver() {
    local DIR=$DATA/puppet
    mkdir -p $DIR

    local CUR=/etc/puppet/fileserver.conf
    local NEW=$DATA/fileserver.conf

    $MAIN puppet_fileserver $CFGDIR/puppet_fileserver.template $DATA/ssh > $NEW
    mv $NEW $CUR
}

gen_puppet_ssh() {
    local hosts=$($MAIN puppet_list)
    for host in $hosts; do
        local DIR=$DATA/ssh/$host
        if ! [ -d $DIR ]; then
            (umask 077; mkdir -p $DIR)
            ssh-keygen -t rsa -C "root@$host" -f $DIR/ssh_host_rsa_key -N ""
            ssh-keygen -t dsa -C "root@$host" -f $DIR/ssh_host_dsa_key -N ""
            chown -R puppet.puppet $DIR
        fi
    done
}

get_ssh_known_hosts() {
    (
        $MAIN ssh_known_hosts urgu.org 194.226.244.126 | while read name line; do
            local DIR=$DATA/ssh/$name
            if [ -d $DIR ]; then
                echo -n "$line "
                cut -f1-2 -d' ' $DIR/ssh_host_rsa_key.pub
                echo -n "$line "
                cut -f1-2 -d' ' $DIR/ssh_host_dsa_key.pub
            fi
        done
    ) > /var/www/urgu.org/https/known_hosts
}

mkdir -p $DATA

gen_dhcp
gen_dns

gen_puppet_cfg
gen_puppet_fileserver
gen_puppet_ssh

get_ssh_known_hosts
