from cmd import add_cmd
import json

@add_cmd('disk', False, 0)
def gen_disk(state):
    rv = {}
    for host in state.hosts:
        if 'disk_layout' in host.props:
            rv[host.name] = host.props['disk_layout']
    return json.dumps(rv, sort_keys=True, indent=4)
