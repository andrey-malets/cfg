import jinja2, json
from cmd import add_cmd

@add_cmd('slurm', True, 1)
def gen_slurm(state, template, facts_path):
    for host in state.hosts:
        try:
            host.facts = None
            with open('%s/%s' % (facts_path, host.name)) as facts:
                host.facts = json.load(facts)
        except Exception as e:
            pass # that's OK

    def matches(host): return 'managed' in host.props
    def get_matching(hosts): return filter(matches, hosts)

    default = state.defaults.slurm
    hosts = get_matching(state.hosts)

    groups = {}
    for group in filter(lambda group: len(get_matching(group.hosts)) > 0, state.groups):
        groups[group.name] = map(lambda host: host.sname, get_matching(group.hosts))

    return jinja2.Template(template).render(hosts=hosts,
                                            groups=groups,
                                            default=default)
