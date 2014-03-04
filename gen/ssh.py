import jinja2
from cmd import add_cmd

from iptables import get_pub_port

@add_cmd('ssh_known_hosts', False, 2)
def gen(state, ext_host, ext_addr):
    lines = []
    def get_names(patt, host):
        rv = [patt % host.name, patt % host.sname, patt % host.addr]
        rv.extend(map(lambda alias: patt % alias, host.aliases))
        rv.extend(map(lambda alias: patt % alias, host.saliases))
        return rv

    for host in state.hosts:
        names = []
        if 'ssh' in host.services or 'unix' in host.services:
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

        if len(names):
            lines.append('%s %s' % (host.name, ','.join(names)))
    return '\n'.join(lines)
