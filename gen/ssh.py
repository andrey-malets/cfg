import jinja2
from cmd import add_cmd

from iptables import get_pub_port

@add_cmd('ssh_known_hosts', False, 2)
def gen(state, ext_host, ext_addr):
    lines = []
    for host in state.hosts:
        names = []
        if 'ssh' in host.services or 'rssh' in host.services:
            names.append(host.name)
            names.append(host.sname)
            names.append(host.addr)
        if 'rssh' in host.services:
            names.append('[%s]:%s' % (ext_host, get_pub_port(host)))
            names.append('[%s]:%s' % (ext_addr, get_pub_port(host)))

        if len(names):
            lines.append('%s %s' % (host.name, ','.join(names)))
    return '\n'.join(lines)
