#!/bin/bash

BASE=`dirname $0`
MAIN="python ./main.py"
DATA=/var/lib/cfg

export CFG=$BASE/cfg/conf.yaml

gen_dhcp() {
    CONF=/etc/dhcp/dhcpd.conf
    $MAIN dhcp $BASE/cfg/dhcp.template > $CONF.new
}

mkdir -p $DATA
