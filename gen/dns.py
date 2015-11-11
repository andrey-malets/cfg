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
    def matches(name):
        return name.find('.') == name.find(zone) - 1
    for host in state.hosts:
        if matches(host.name) and host.addr != None:
            yield (host.sname, 'A', host.addr)
            for salias in host.saliases:
                yield (salias, 'CNAME', host.sname)
        backends = []
        if 'backend_for' in host.props:
            prop = host.props['backend_for']
            backends = [prop] if type(prop) == str else prop
        for backend in filter(matches, backends):
            yield(backend.split('.')[0], 'A', state.find(
                state.get_canonical_hostname(state.defaults.frontend)).addr)

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
