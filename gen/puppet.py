import jinja2
from itertools import chain
from cmd import add_cmd

@add_cmd('puppet_cfg', True, 0)
def gen(state, template):
    targets = filter(lambda host: (
        'services' in host.props and
        'puppet-ssh' in host.props['services']), state.hosts)

    return jinja2.Template(template).render(hosts=targets)

@add_cmd('puppet_fileserver', True, 1)
def gen(state, template, prefix):
    targets = filter(lambda host: (
        'services' in host.props and
        'puppet-ssh' in host.props['services']), state.hosts)

    return jinja2.Template(template).render(hosts=targets, prefix=prefix)

@add_cmd('puppet_list', False, 0)
def gen(state):
    targets = filter(lambda host: (
        'services' in host.props and
        'puppet-ssh' in host.props['services']), state.hosts)

    return '\n'.join(map(lambda host: host.name, targets))
