import jinja2
from itertools import chain
from cmd import add_cmd

@add_cmd('dhcp', True, 0)
def gen_dhcp(state, template):
    def get_entries(host):
        def get_entry(name, mac):
            return {'name'     : name,
                    'hostname' : host.sname,
                    'mac'      : mac,
                    'addr'     : host.addr,
                    'params'   : host.props.get('dhcp', {})}

        if len(host.macs) == 1:
            yield get_entry(host.sname, host.macs[0])
        else:
            for i in xrange(len(host.macs)):
                yield get_entry('%s-%d' % (host.sname, i+1), host.macs[i])

    return jinja2.Template(template).render(networks=state.networks,
        hosts=chain.from_iterable(map(get_entries, state.hosts)))
