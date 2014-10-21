import jinja2
from cmd import add_cmd
from parse.host import get_sname_dups

@add_cmd('slurm', True, 1)
def gen_slurm(state, template, facts_path):
    state.parse_facts(facts_path)

    default = state.defaults.slurm
    def get_matching(hosts): return filter(lambda host: default in host.props, hosts)

    hosts = get_matching(state.hosts)

    dups = get_sname_dups(hosts)
    assert len(dups) == 0, ("cannot generate SLURM config with duplicate "
        + "short names for hosts %s" % ", ".join(dups))

    groups = {}
    for group in filter(lambda group: len(get_matching(group.hosts)) > 0, state.groups):
        groups[group.name] = map(lambda host: host.sname, get_matching(group.hosts))

    return jinja2.Template(template).render(hosts=hosts,
                                            groups=groups,
                                            default=default)
