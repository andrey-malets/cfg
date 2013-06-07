import jinja2
from itertools import chain

def get_dns_name(host):
    return host.name.split('.')[0]

def get_rname(host, network):
    parts = host.addr.split('.')
    parts.reverse()
    return '.'.join(parts[0:(32 - network.count) / 8])

def all(fn):
    return lambda hosts, template, *args: jinja2.Template(template).render(
        hosts=chain.from_iterable(map(lambda host: fn(host, *args), hosts)))

@all
def gen_fwd(host, zone):
    if host.name.find('.') == host.name.find(zone) - 1:
        yield {'name'    : get_dns_name(host),
               'addr'    : host.addr,
               'aliases' : host.saliases}

@all
def gen_reverse(host, network):
    assert (network.count % 8) == 0, ('not supported for %d' % network.count)
    if network.has(host.addr):
        yield {'name' : host.name, 'addr' : get_rname(host, network)}

@all
def gen_fb(host, network):
    for addr in host.fb:
        if network.has(addr):
            yield {'name' : get_dns_name(host), 'addr' : addr}
