import jinja2

def gen_fwd(hosts, zone, template):
    params = []
    for host in hosts:
        if host.name.find('.') == host.name.find(zone)-1:
            params.append({'name'   : host.name.split('.')[0],
                           'addr'   : host.addr,
                           'aliases': host.saliases})
    return jinja2.Template(template).render(hosts=params)
