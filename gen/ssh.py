import jinja2
from cmd import add_cmd
import os.path
from parse.host import get_sname_dups

from iptables import get_pub_port

def get_patt(host):
    return ('%s' if 'ssh_port' not in host.props
        else '[%s]:' + str(host.props['ssh_port']))


def get_base_names(host, patt):
    rv = [patt % host.name, patt % host.sname, patt % host.addr]
    rv.extend(map(lambda alias: patt % alias, host.aliases))
    rv.extend(map(lambda alias: patt % alias, host.saliases))
    return rv


def get_all_names(state, host):
    frontend = state.find(state.defaults.frontend)
    names = get_base_names(host, get_patt(host))
    if state.is_gray(host) and not state.belongs_to(host).private:
        names.extend(get_base_names(
            frontend, '[%s]:' + str(get_pub_port(host))))
    if 'tcp_fwd' in host.props and 22 in host.props['tcp_fwd']:
        names.extend(get_base_names(frontend, '[%s]'))
    return names


def get_key(data, host, keytype):
    if 'managed' in host.props:
        filename = os.path.join(
            data, 'ssh', host.name,
            'ssh_host_{}_key.pub'.format(keytype))
        if os.path.isfile(filename):
            with open(filename) as input:
                return input.read().strip().split(' ')[1]
    elif host.facts:
        return host.facts.get('ssh{}key'.format(keytype))
    return None


def get_keyname(keytype):
    return {'rsa': 'ssh-rsa', 'dsa': 'ssh-dss'}[keytype]


@add_cmd('ssh_known_hosts', False, 2)
def gen(state, facts_path, data):
    state.parse_facts(facts_path)

    def matches(host): return 'ssh' in host.services

    dups = get_sname_dups(filter(matches, state.hosts))
    assert len(dups) == 0, ("cannot generate SSH config with duplicate "
        + "short names for hosts %s" % ", ".join(dups))

    lines = []
    for host in filter(matches, state.hosts):
        names = get_all_names(state, host)
        if names and host.facts:
            for keytype in ['rsa', 'dsa']:
                key = get_key(data, host, keytype)
                if key is not None:
                    lines.extend(["{} {} {}".format(name,
                                                    get_keyname(keytype), key)
                                  for name in [host.name] + names])
    return '\n'.join(lines)
