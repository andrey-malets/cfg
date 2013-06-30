import jinja2
from cmd import add_cmd

def get(state):
    return filter(lambda host: 'puppet-ssh' in host.services, state.hosts)

@add_cmd('puppet_cfg', True, 0)
def gen(state, template):
    return jinja2.Template(template).render(hosts=get(state))

@add_cmd('puppet_fileserver', True, 1)
def gen(state, template, prefix):
    return jinja2.Template(template).render(hosts=get(state), prefix=prefix)

@add_cmd('puppet_list', False, 0)
def gen(state):
    return '\n'.join(map(lambda host: host.name, get(state)))
