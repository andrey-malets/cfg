import jinja2
from cmd import add_cmd
from parse.host import get_sname_dups

def clamp(spec):
    for index, (key, value) in enumerate(spec):
        if key in ['RealMemory', 'TmpDisk']:
            spec[index] = (key, int(int(value) * 0.5))

def gen_line(fact):
    spec = filter(
        lambda (key, _): key not in ['ClusterName', 'Procs', 'Boards'],
        [(pair.split('=')) for pair in fact.split(' ')])
    clamp(spec)
    return ' '.join(map(lambda pair: '{}={}'.format(*pair), spec))

@add_cmd('slurm', True, 1)
def gen_slurm(state, template, facts_path):
    state.parse_facts(facts_path)

    default = state.defaults.slurm
    def get_matching(hosts):
        return filter(lambda host: default in host.props, hosts)

    hosts = get_matching(state.hosts)

    dups = get_sname_dups(hosts)
    assert len(dups) == 0, ("cannot generate SLURM config with duplicate "
        + "short names for hosts %s" % ", ".join(dups))

    groups = {}
    for group in state.groups:
        group_hosts = get_matching(host for host, _ in group.hosts)
        if len(group_hosts) > 0:
            groups[group.name] = map(lambda host: host.sname, group_hosts)

    return jinja2.Template(template).render(hosts=hosts,
                                            groups=groups,
                                            default=default,
                                            get_line=gen_line)
