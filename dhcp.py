import jinja2

def gen(hosts, networks, template):
    def get_entries(host):
        if not host.addr or not len(host.macs): return
        def get_entry(host, name, mac):
            return {
                'name'     : name,
                'hostname' : host.sname.split('.')[0],
                'mac'      : mac,
                'addr'     : host.addr,
                'params' : ({} if not 'dhcp' in host.props
                            else host.props['dhcp'])
            }
        if len(host.macs) == 1:
            yield get_entry(host, host.sname, host.macs[0])
        else:
            for i in xrange(0, len(host.macs)):
                yield get_entry(host, '%s-%d' %
                    (host.sname, i+1), host.macs[i])

    entries = []
    for host in hosts:
        entries.extend(get_entries(host))
    
    return jinja2.Template(template).render(hosts=entries, networks=networks)
