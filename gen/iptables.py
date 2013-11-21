from cmd import add_cmd

def get_pub_port(host):
    comps = host.addr.split('.')
    return int(comps[2]) * 1000 + int(comps[3])

@add_cmd('ipt_ports', False, 2)
def gen_ports(state, dst, chain):
    def tcp_forwardings(host):
        def matches(host):
            return state.is_gray(host) and not state.belongs_to(host).private

        rv = host.props.get('tcp_fwd', {})
        if matches(host):
            if 'ssh' in host.services or 'unix' in host.services:
                rv[get_pub_port(host)] = 22
            if 'rrdp' in host.services:
                rv[get_pub_port(host)] = 3389
        return rv

    def udp_forwardings(host):
        return host.props.get('udp_fwd', {})

    lines = ["iptables -t nat -F %s" % chain]
    def add(proto, srcport, dstport):
        lines.append("iptables -t nat -A %(chain)s\
                          -p %(proto)s -m state --state NEW \
                          -d %(dst)s --dport %(srcport)d\
                          -j DNAT --to-destination %(ip)s:%(dstport)d"
                           % { 'chain'   : chain,
                               'dst'     : dst,
                               'srcport' : srcport,
                               'proto'   : proto,
                               'ip'      : host.addr,
                               'dstport' : dstport })

    for host in state.hosts:
        for srcport, dstport in tcp_forwardings(host).iteritems(): add('tcp', srcport, dstport)
        for srcport, dstport in udp_forwardings(host).iteritems(): add('udp', srcport, dstport)

    return '\n'.join(lines)
