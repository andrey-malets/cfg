#!/bin/bash -e

BASE=$(dirname "$0")
MAIN="python $BASE/main.py"
SERIAL="python $BASE/util/serial.py"
ROUTER_ATTRS="$BASE/util/router-attrs.sh"
DATA=/var/lib/cfg

FACTS=$DATA/facts
CFGDIR=$BASE/cfg

export CFG=$CFGDIR/conf.yaml

ROUTER_HOST=dijkstra.urgu.org
ROUTER_IP=194.226.244.126

cmp_files() {
    set +e; cmp -s $1 $2; local rv=$?; set -e
    return $rv
}

gen_dhcp() {
    local CUR=/etc/dhcp/dhcpd.conf
    local NEW=$DATA/dhcpd.conf

    $MAIN dhcp $CFGDIR/dhcp.template > $NEW

    if ! cmp_files $CUR $NEW; then
        mv $NEW $CUR
        /etc/init.d/isc-dhcp-server restart
    else
        rm $NEW
    fi
}

gen_dns() {
    local ZONES="urgu.org"
    local RELOAD=0 RESTART=0

    gen_zone() {
        local ZONE=$1 CMD=$2 TEMPLATE=$3

        local SFILE=$DATA/$ZONE.serial
        local CUR=$DATA/$ZONE.master
        local OLD=$CUR.old NEW=$CUR.new

        set +e; SOLD=$($SERIAL get $SFILE 2>/dev/null); rv=$?; set -e
        if [ $rv -ne 0 ]; then
            RELOAD=1
            local SNEW=$($SERIAL inc $SFILE)
            $MAIN $CMD $TEMPLATE $SNEW $ZONE > $CUR
        else
            $MAIN $CMD $TEMPLATE $SOLD $ZONE > $OLD
            if ! cmp_files $CUR $OLD; then
                RELOAD=1
                rm $OLD
                SNEW=$($SERIAL inc $SFILE)
                $MAIN $CMD $TEMPLATE $SNEW $ZONE > $NEW
                mv $NEW $CUR
            else
                rm $OLD
            fi
        fi
    }

    for ZONE in $ZONES; do
        gen_zone $ZONE dns $CFGDIR/$ZONE.template
    done

    for NET in $($MAIN rdns_nets); do
        gen_zone $NET rdns $CFGDIR/reverse.template
    done

    local CUR=$DATA/reverse.config
    local NEW=$DATA/reverse.config.new

    $MAIN rdns_cfg $CFGDIR/rdns_cfg.template $DATA/%s.master /etc/bind/db.empty > $NEW

    if ! cmp_files $CUR $NEW; then
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

gen_iptables_ports() {
    local CUR=$DATA/ipt_ports.sh
    local NEW=$CUR.new

    $MAIN ipt_ports $ROUTER_IP server > $NEW

    if ! cmp_files $CUR $NEW; then
        mv $NEW $CUR
        bash $CUR
        /etc/init.d/iptables save active
    else
        rm $NEW
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
    local NEW=$DIR/fileserver.conf

    $MAIN puppet_fileserver $CFGDIR/puppet_fileserver.template $DATA/ssh > $NEW
    mv $NEW $CUR
}

gen_puppet_ssh() {
    local hosts=$($MAIN puppet_managed)
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

gen_nagios() {
    local DIR=$DATA/nagios
    mkdir -p $DIR

    local CUR=$DIR/nagios.cfg
    local NEW=$DIR/nagios.cfg.new

    $MAIN nagios $CFGDIR/nagios.template > $NEW

    if ! cmp_files $CUR $NEW; then
        mv $NEW $CUR
        /etc/init.d/nagios3 restart
    else
        rm $NEW
    fi
}

gen_ssh_known_hosts() {
    (
        $MAIN ssh_known_hosts $ROUTER_HOST $ROUTER_IP | while read name line; do
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

gather_ssh_known_hosts() {
    local URL="https://$ROUTER_HOST:8140/production"
    local WGET="wget -O-
        --header=Accept:yaml
        --certificate /var/lib/puppet/ssl/certs/$ROUTER_HOST.pem
        --private-key /var/lib/puppet/ssl/private_keys/$ROUTER_HOST.pem
        --ca-certificate /var/lib/puppet/ssl/certs/ca.pem"

    $WGET $URL/facts_search/search 2>/dev/null | awk '{print $2}' | grep -v '^$' |\
    while read host; do
        local DIR=$DATA/ssh/$host
        if ! [ -d $DIR ]; then
            mkdir -p $DIR
            $WGET $URL/facts/$host 2>/dev/null | grep sshrsakey |\
                awk "{print \"ssh-rsa\",\$2,\"root@$host\"}" > $DIR/ssh_host_rsa_key.pub
            $WGET $URL/facts/$host 2>/dev/null | grep sshdsakey |\
                awk "{print \"ssh-dss\",\$2,\"root@$host\"}" > $DIR/ssh_host_dsa_key.pub
            chown -R puppet.puppet $DIR
        fi
    done
}

refresh_facts() {
    get_wget() {
        echo "wget
            --header=Accept:$2
            --certificate /var/lib/puppet/ssl/certs/$1.pem
            --private-key /var/lib/puppet/ssl/private_keys/$1.pem
            --ca-certificate /var/lib/puppet/ssl/certs/ca.pem"
    }

    local URL="https://$ROUTER_HOST:8140/production"
    local WGET=$(get_wget $ROUTER_HOST yaml)

    mkdir -p $FACTS

    $WGET -O - $URL/facts_search/search 2>/dev/null | awk '{print $2}' | grep -v '^$' |\
    while read host; do
        WGET=$(get_wget $ROUTER_HOST pson)
        $WGET -O $FACTS/$host $URL/facts/$host 2>/dev/null
    done
    chown -R puppet.puppet $FACTS
}

gen_ssh_known_hosts_updater() {
    (
cat <<END
#!/bin/bash

# usage (e.g. in crontab): [curl|wget -O-] https://ssl.urgu.org/known_hosts.sh | bash -s -- -y

args=\$(getopt yf: \$*)
set -- \$args

auto=0

if [ \$(whoami) == root ]; then
    known_hosts_file=/etc/ssh/ssh_known_hosts
else
    known_hosts_file=~/.ssh/known_hosts
fi

for arg in \$args; do
    case "\$arg" in
        -y)
            auto=1
            shift ;;
        -f)
            known_hosts_file=\$2
            shift ;;
    esac
done

echo >&2 working with \$known_hosts_file

temp_file=\${known_hosts_file}.new
if [ -r \$known_hosts_file ]; then
    cp \$known_hosts_file \$temp_file
else
    touch \$temp_file
fi

declare -a script

END

    $MAIN ssh_known_hosts $ROUTER_HOST $ROUTER_IP | while read name line; do
        local DIR=$DATA/ssh/$name
        if [ -d $DIR ]; then
            read newtype newkey newcomment < $DIR/ssh_host_rsa_key.pub
            echo "$line," | while read -d, item; do
cat <<END

# echo working with $item
script[\${#script[@]}]=\$(
    ssh-keygen -F $item -f \$temp_file | grep -v '#' | (
        changed=0; seen=0;
        while read host type key comment; do
            seen=1
            if [ \$type == $newtype ] && [ \$key != $newkey ]; then
                changed=1
            fi
        done
        if [ \$seen -ne 0 ]; then
            if [ \$changed -ne 0 ]; then
                echo >&2 "warning: some $newtype key(s) for $item changed, replacing";
                echo "ssh-keygen -R $item -f \$temp_file 2>/dev/null; rm \${temp_file}.old; \
                    echo $item $newtype $newkey $newcomment >> \$temp_file; "
            fi
        else
            echo >&2 "info: adding new $newtype key for $item"
            echo "echo $item $newtype $newkey $newcomment >> \$temp_file; "
        fi
    )
)

END
            done
        fi
    done

cat <<END

for i in \$(seq 1 \${#script[@]}); do
    bash -ec "\${script[i-1]}"
done

if [ \$auto -ne 0 ]; then
    mv \$temp_file \$known_hosts_file
    chmod 644 \$known_hosts_file
else
    read -p 'Commit? ' y
    case \$y in
        [Yy]*)  mv \$temp_file \$known_hosts_file
                chmod 644 \$known_hosts_file
        ;;

        *)      rm \$temp_file
        ;;
    esac
fi

END

    ) >      $DATA/known_hosts.sh
    chmod +x $DATA/known_hosts.sh

    cp -f $DATA/known_hosts.sh /etc/puppet/files
}

gen_slurm() {
    $MAIN slurm $CFGDIR/slurm.template $FACTS > $DATA/slurm.conf
    cp -f $DATA/slurm.conf /etc/puppet/files
}

gen_ext_http() {
    local CUR=$DATA/ext_http
    local NEW=$DATA/ext_http.new
    local KEYPATH=$DATA/https

    ln -sf $CUR /etc/nginx/sites-enabled
    $MAIN ext_http $CFGDIR/ext_http.template $KEYPATH > $NEW

    if ! cmp_files $CUR $NEW; then
        mv $NEW $CUR
        /etc/init.d/nginx restart
    else
        rm $NEW
    fi
}

gen_http_back() {
    local CUR=$DATA/http_back
    local NEW=$DATA/http_back.new
    local KEYPATH=$DATA/https

    ln -sf $CUR /etc/nginx/sites-enabled
    $MAIN http_back $CFGDIR/http_back.template $KEYPATH > $NEW

    if ! cmp_files $CUR $NEW; then
        mv $NEW $CUR
        /etc/init.d/nginx restart
    else
        rm $NEW
    fi
}

reset_https_ca() {
    local DIR="$DATA/https"
    local KEY="$DIR/ca.key" CRT="$DIR/ca.crt"

    local PWD
    read -s -p 'Password:' PWD

    local CN="$ROUTER_HOST"

    rm -rf "$DIR"
    mkdir -p "$DIR/"{,certs,crl,newcerts,private}
    echo '01' > "$DIR/serial"
    touch "$DIR/index.txt"

    chown www-data: "$DIR"
    chmod 500 "$DIR"

    openssl genrsa -des3 -out "$KEY" -passout env:PWD 2048
    chmod 600 "$KEY"
    openssl req -new -x509 -days $((365*3)) -key "$KEY" -passin env:PWD -config \
        <($MAIN https_req $CFGDIR/https_req.template "$ROUTER_HOST" "$CN") \
        -out "$CRT" -batch
    cp "$CRT" /etc/puppet/files
}

gen_https_certs() {
    local DIR="$DATA/https"
    local CA_KEY="$DIR/ca.key" CA_CRT="$DIR/ca.crt"

    local PWD
    read -s -p 'Password:' PWD

    $MAIN https | while read hostspec; do
        local hostname=${hostspec%%,*} cn=${hostspec##*,}
        local KEY="$DIR/$cn.key" CRT="$DIR/$cn.crt" REQ="$DIR/$cn.req"
        if [[ ! -f "$CRT" ]]; then
            openssl req -nodes -newkey rsa:1024 -keyout "$KEY" -out "$REQ" -batch \
                -config <($MAIN https_req $CFGDIR/https_req.template "$hostname" "$cn")
            openssl ca -out "$CRT" -passin env:PWD -in "$REQ" -keyfile "$CA_KEY" \
                -config <($MAIN https_ca $CFGDIR/https_ca.template "$DIR") -batch
        fi
    done
}

gen_ups_mrtg() {
    local OUTPUT="$DATA"/ups_mrtg.cfg
    $MAIN ups_mrtg $CFGDIR/mrtg.template > $OUTPUT
}

gen_user_chains() {
    local ipp=/etc/openvpn/runc/ipp.txt iface=tun0 target=UaA
    python "$BASE/util/iptables_users.py" "$ipp" "$iface" "$target" | sh -s
}

mkdir -p $DATA

export ROUTER_DEV=$($ROUTER_ATTRS dev)
export ROUTER_SRC=$($ROUTER_ATTRS src)

almost_all() {
    gen_dhcp
    gen_dns
    gen_iptables_ports

    gen_puppet_cfg
    gen_puppet_fileserver
    gen_puppet_ssh

    gather_ssh_known_hosts

    gen_ssh_known_hosts
    gen_ssh_known_hosts_updater

    gen_nagios
    gen_slurm

    gen_ext_http
    gen_http_back

    gen_ups_mrtg
}

all() {
    refresh_facts
    almost_all
}

if [ $# -eq 0 ]; then
    almost_all
else
    cmd=$1; shift
    $cmd "$@"
fi
