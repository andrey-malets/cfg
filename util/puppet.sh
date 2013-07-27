#!/bin/bash -e

host=$1

ssh="ssh -o GlobalKnownHostsFile=/dev/null -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no"
scp="scp -o GlobalKnownHostsFile=/dev/null -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no"

$ssh $host "rm -rf puppet"
$ssh $host "umask 077; mkdir puppet"
$ssh $host "mkdir puppet/certs"
$ssh $host "umask 027; mkdir puppet/private_keys"

if ! [ -e /var/lib/puppet/ssl/certs/$host.pem ]; then
    puppetca generate $host
fi

$scp /var/lib/puppet/ssl/certs/ca.pem $host:puppet/certs
$scp /var/lib/puppet/ssl/certs/$host.pem $host:puppet/certs
$scp /var/lib/puppet/ssl/private_keys/$host.pem $host:puppet/private_keys

$ssh $host "./conf.sh cp -r puppet {}; rm -rf puppet"

$ssh $host reboot
