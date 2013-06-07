def get_pub_port(host):
    comps = host.addr.split('.')
    return int(comps[2]) * 1000 + int(comps[3])
        
def gen_ports(hosts, dst, chain):
    def matches(host):
        return (host.addr != None
            and host.addr.startswith('172.16.')
            and (not host.addr.startswith('172.16.9.'))
            and 'services' in host.props
            and ('ssh' in host.props['services']
              or 'rdp' in host.props['services']))

    def get_priv(host):
        return 22 if 'ssh' in host.props['services'] else 3389

    yield "iptables -t nat -F %s\n" % chain
    for host in filter(matches, hosts):
        yield ("iptables -t nat -A %(chain)s\
                         -d %(dst)s --dport %(pub)d\
                         -p tcp -m state --state NEW\
                         -j DNAT --to-destination %(ip)s:%(priv)d\n"
                % { 'chain' : chain,
                    'dst'   : dst,
                    'pub'   : get_pub_port(host),
                    'ip'    : host.addr,
                    'priv'  : get_priv(host) })
