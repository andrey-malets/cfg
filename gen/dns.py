import jinja2
from itertools import chain
from cmd import add_cmd

def get_rname(host, network):
    parts = host.addr.split('.')
    parts.reverse()
    return '.'.join(parts[0:(32 - network.count) / 8])

def dns_fn(fn):
    return (lambda state, template, serial, *args:
        jinja2.Template(template).render(records=fn(state, *args), serial=serial))

@add_cmd('dns', True, 2)
@dns_fn
def gen_fwd(state, zone):
    for host in state.hosts:
        if host.name.find('.') == host.name.find(zone) - 1:
            yield (host.sname, 'A', host.addr)
            for alias in host.saliases:
                yield (alias, 'CNAME', host.sname)

@add_cmd('rdns', True, 2)
@dns_fn
def gen_reverse(state, net_name):
    network = state.choose_net(net_name)
    assert network.is_classful(), ('not supported for classless mask /%d' % network.count)
    for host in filter(lambda host: host.addr != None, state.hosts):
        if network.has(host.addr):
            yield (get_rname(host, network), 'PTR', host.name + '.')

@add_cmd('dns_fb', True, 2)
@dns_fn
def gen_fb(state, net_name):
    network = state.choose_net(net_name)
    for host in state.hosts:
        for addr in host.fb:
            if network.has(addr):
                pass
                #TODO(malets):
#                yield {'name'    : host.sname,
#                       'addr'    : addr,
#                       'aliases' : host.saliases}
