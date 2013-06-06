import jinja2

def gen_fwd(hosts, zone, template):
    params = []
    for host in hosts:
        if host.name.find('.') == host.name.find(zone)-1:
            params.append({'name'   : host.name.split('.')[0],
                           'addr'   : host.addr,
                           'aliases': host.saliases})
    return jinja2.Template(template).render(hosts=params)

def get_rname(host, network):
    parts = host.addr.split('.')
    parts.reverse()
    return '.'.join(parts[0:(32 - network.count) / 8])

def gen_reverse(hosts, network, template):
    params = []
    #assert (network.count % 8) == 0
    for host in hosts:
        if host.addr != None and network.has(host):
            params.append({'name'   : host.name,
                           'addr'   : get_rname(host, network)})
    return jinja2.Template(template).render(hosts=params)
