import jinja2
from cmd import add_cmd
from parse.host import get_sname_dups

def get(state):
    return filter(lambda host: 'managed' in host.props, state.hosts)

@add_cmd('puppet_cfg', True, 0)
def gen(state, template):
    return jinja2.Template(template).render(state=state)

@add_cmd('puppet_fileserver', True, 1)
def gen(state, template, prefix):
    dups = get_sname_dups(filter(lambda host: 'managed' in host.props, state.hosts))
    assert len(dups) == 0, ("cannot generate puppet fileserver config "
        + "with duplicate short names for hosts %s" % ", ".join(dups))

    return jinja2.Template(template).render(hosts=get(state), prefix=prefix)

@add_cmd('puppet_managed', False, 0)
def gen(state):
    return '\n'.join(map(lambda host: host.name, get(state)))
