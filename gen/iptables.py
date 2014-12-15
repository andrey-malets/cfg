from cmd import add_cmd

def init(table, chain):
    print ("if iptables -t '%s' -L '%s' 2>/dev/null >/dev/null; "
        "then iptables -t '%s' -F '%s'; "
        "else iptables -t '%s' -N '%s'; fi" % ((table, chain) * 3))

def cn2chain(cn):
    return 'openvpn_%s' % cn

def gn2chain(cn):
    return 'group_%s' % cn

class Rule:
    def __init__(self, chain, target):
        self.chain  = chain
        self.target = target

        self.new    = None
        self.dest   = None
        self.proto  = None
        self.dport  = None

    def set_new(self):
        self.new = '-m state --state NEW'
        return self

    def set_dest(self, dest):
        self.dest = "-d '%s'" % dest
        return self

    def set_proto(self, proto):
        self.proto = "-p '%s'" % proto
        return self

    def set_dport(self, dport):
        self.dport = "--dport '%s'" % dport
        return self

    def format(self):
        restrictions = ''
        for restriction in [self.new, self.dest, self.proto, self.dport]:
            if restriction != None:
                restrictions += (' ' + restriction)
        return "iptables -A '{}'{} -j '{}'".format(
            self.chain, restrictions, self.target)

def put_if_exists(user, rule):
    print ("iptables -L '%s' 2>/dev/null >/dev/null && %s" %
        (cn2chain(user), rule.format()))

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

def add_base_access(rule, host):
    return rule.set_new().set_dest(host.addr)

def add_vnc_access(rule, host, vnc_port):
    port = 5900 + vnc_port
    return add_base_access(rule, host).set_proto('tcp').set_dport(port)

def add_ssh_access(rule, host):
    return add_base_access(rule, host).set_proto('tcp').set_dport(22)

def add_access(rule, host, service):
    mapping = {'full': add_base_access, 'ssh': add_ssh_access}
    assert service in mapping, 'unknown access "%s"' % service
    return mapping[service](rule, host)

def gen_admin_access(state, host, chain):
    if not host.admin:
        return
    network = state.belongs_to(host)
    if network and network.private and host.addr:
        rule = Rule(chain, cn2chain(host.admin)).set_new().set_dest(host.addr)
        put_if_exists(host.admin, rule)
    vm_host = host.vm_host
    if vm_host:
        vms = vm_host.facts['pyxendomains']
        assert(vms and host.sname in vms)
        vm_descr = vms[host.sname]
        listen = vm_descr.get('vnclisten', None)
        if listen:
            vnc_port = int(listen.split(':')[1])
            rule = add_vnc_access(Rule(chain, cn2chain(host.admin)),
                                  vm_host, vnc_port)
            put_if_exists(host.admin, rule)

def gen_user_access(state, host, chain):
    if 'access' in host.props:
        for spec, service in host.props['access'].iteritems():
            if state.is_user(spec):
                rule = Rule(chain, cn2chain(spec))
                put_if_exists(spec, add_access(rule, host, service))
            else:
                rule = Rule(chain, gn2chain(spec))
                print add_access(rule, host, service).format()

@add_cmd('ipt_access', False, 2)
def gen_access(state, chain, facts_path):
    state.parse_facts(facts_path)

    init('filter', chain)
    for user_group, users in state.user_groups.iteritems():
        group_chain = gn2chain(user_group)
        init('filter', group_chain)
        for user in users:
            put_if_exists(user, Rule(group_chain, cn2chain(user)))

    for host in state.hosts:
        gen_admin_access(state, host, chain)
        gen_user_access(state, host, chain)
    return ""
