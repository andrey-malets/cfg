from cmd import add_cmd
import jinja2

def filter_nets(state, prop):
    return filter(lambda net: prop in net.props, state.networks)

def fmt_nets(nets):
    return '\n'.join(map(lambda net: net.get_addr(), nets))

@add_cmd('fb_nets', False, 0)
def list_nets(state):
    return fmt_nets(filter_nets(state, 'fb'))

@add_cmd('rdns_nets', False, 0)
def list_nets(state):
    return fmt_nets(filter_nets(state, 'rdns'))

@add_cmd('rdns_cfg', True, 2)
def rdns_cfg(state, template, patt, empty):
    nets = {}
    for n in range(16, 32):
        nets['%d.172.in-addr.arpa' % n] = empty
    for net in filter_nets(state, 'rdns'):
        nets[net.get_rdns_zone()] = patt % net.get_addr()
    return jinja2.Template(template).render(networks=nets,empty=empty)

@add_cmd('router', False, 1)
def choose_router(state, addr):
    return state.choose_router(addr)

@add_cmd('etherwake', False, 1)
def etherwake(state, hostname):
    host = state.find(hostname)
    if host != None and len(host.macs):
        network = state.belongs_to(host)
        if network and network.iface:
            return 'etherwake -i %s %s' % (network.iface, host.macs[0])
        raise Exception('could not find network')
    else:
        raise Exception('could not find host')
