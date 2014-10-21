from cmd import add_cmd

def init(table, chain):
    print ('if iptables -t %s -L %s 2>/dev/null >/dev/null; '
        'then iptables -t %s -F %s; '
        'else iptables -t %s -N %s; fi' % ((table, chain) * 3))

def cn2chain(cn):
    return 'openvpn_%s' % cn

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

@add_cmd('ipt_access', False, 2)
def gen_access(state, chain, facts_path):
    def put_if_exists(user, rule):
        return ('iptables -L "%s" 2>&1 >/dev/null && iptables -A "%s" %s -j "%s"' %
            (cn2chain(user), chain, rule, cn2chain(user)))
    state.parse_facts(facts_path)
    init('filter', chain)
    for host in state.hosts:
        network = state.belongs_to(host)
        if not host.admin:
            continue
        if network and network.private and host.addr:
            print put_if_exists(host.admin, '-d "%s" -m state --state NEW' % host.addr)
        vm_host = host.vm_host
        if vm_host:
            vms = vm_host.facts['pyxendomains']
            assert(vms and host.sname in vms)
            vm_descr = vms[host.sname]
            if 'vnclisten' in vm_descr:
                port = 5900 + int(vm_descr['vnclisten'].split(':')[1])
                print put_if_exists(
                    host.admin,
                    '-d "%s" -p tcp -m state --state NEW --dport %d' % (
                        vm_host.addr, port))
    return ""
