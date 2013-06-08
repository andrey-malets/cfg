import jinja2
from itertools import chain

def gen(hosts, template, networks):
    def get_entries(host):
        if not host.addr or not len(host.macs): return
        def get_entry(host, name, mac):
            return { 'name'     : name,
                     'hostname' : host.sname,
                     'mac'      : mac,
                     'addr'     : host.addr,
                     'params'   : host.props.get('dhcp', {})}

        if len(host.macs) == 1:
            yield get_entry(host, host.sname, host.macs[0])
        else:
            for i in xrange(0, len(host.macs)):
                yield get_entry(host, '%s-%d' %
                    (host.sname, i+1), host.macs[i])

    return jinja2.Template(template).render(networks=networks,
        hosts=chain.from_iterable(map(get_entries, hosts)))
