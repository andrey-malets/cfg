import jinja2
from cmd import add_cmd

@add_cmd('slurm', True, 0)
def gen_slurm(state, template):
    def matches(host): return 'managed' in host.props
    def get_matching(hosts): return map(lambda host: host.sname, filter(matches, hosts))

    default = state.defaults.slurm
    hosts = get_matching(state.hosts)
    groups = {}
    for group in filter(lambda group: len(get_matching(group.hosts)) > 0, state.groups):
        groups[group.name] = get_matching(group.hosts)

    return jinja2.Template(template).render(hosts=hosts, groups=groups, default=default)
