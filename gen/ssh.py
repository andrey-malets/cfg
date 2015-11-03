import jinja2
from cmd import add_cmd
from parse.host import get_sname_dups

from iptables import get_pub_port

@add_cmd('ssh_known_hosts', False, 3)
def gen(state, facts_path, ext_host, ext_addr):
    state.parse_facts(facts_path)

    lines = []
    def get_names(patt, host):
        rv = [patt % host.name, patt % host.sname, patt % host.addr]
        rv.extend(map(lambda alias: patt % alias, host.aliases))
        rv.extend(map(lambda alias: patt % alias, host.saliases))
        return rv

    def matches(host): return 'ssh' in host.services

    dups = get_sname_dups(filter(matches, state.hosts))
    assert len(dups) == 0, ("cannot generate SSH config with duplicate "
        + "short names for hosts %s" % ", ".join(dups))

    for host in filter(matches, state.hosts):
        names = []
        patt = ('%s' if 'ssh_port' not in host.props
                     else '[%s]:' + str(host.props['ssh_port']))
        names.extend(get_names(patt, host))
        if state.is_gray(host) and not state.belongs_to(host).private:
            names.append('[%s]:%s' % (ext_host, get_pub_port(host)))
            names.append('[%s]:%s' % (ext_addr, get_pub_port(host)))
        if 'tcp_fwd' in host.props and 22 in host.props['tcp_fwd']:
            fronts = filter(lambda host: host.name == ext_host, state.hosts)
            if len(fronts) == 1:
                names.extend(get_names('%s', fronts[0]))

        if names and host.facts:
            for keytype in ['rsa', 'dsa', 'ecdsa', 'ed25519']:
                key = host.facts.get('ssh{}key'.format(keytype))
                if key:
                    lines.extend(["{} ssh-{} {}".format(name, keytype, key)
                                  for name in [host.name] + names])
    return '\n'.join(lines)
