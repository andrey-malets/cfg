import jinja2

def gen_fwd(hosts, zone, template):
    params = []
    for host in hosts:
        if host.name.find('.') == host.name.find(zone) - 1:
            params.append({'name'    : host.name.split('.')[0],
                           'addr'    : host.addr,
                           'aliases' : host.saliases})
    return jinja2.Template(template).render(hosts=params)

def get_rname(host, network):
    parts = host.addr.split('.')
    parts.reverse()
    return '.'.join(parts[0:(32 - network.count) / 8])

def gen_reverse(hosts, network, template):
    params = []
    assert (network.count % 8) == 0, ('not supported for %d' % network.count)
    for host in hosts:
        if network.has(host.addr):
            params.append({'name' : host.name,
                           'addr' : get_rname(host, network)})
    return jinja2.Template(template).render(hosts=params)

def gen_fb(hosts, network, template):
    params = []
    for host in hosts:
        for addr in host.fb:
            if network.has(addr):
                params.append({'name' : host.name.split('.')[0],
                               'addr' : addr})
    return jinja2.Template(template).render(hosts=params)
