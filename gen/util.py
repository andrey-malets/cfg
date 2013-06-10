from cmd import add_cmd

def filter_nets(state, prop):
    return filter(lambda net: prop in net.props, state.networks)

def fmt_nets(nets):
    return '\n'.join(map(lambda net: net.get_addr(), nets))

@add_cmd('list_rdns_nets', False, 0)
def list_nets(state):
    return fmt_nets(filter_nets(state, 'rdns'))

@add_cmd('list_fb_nets', False, 0)
def list_nets(state):
    return fmt_nets(filter_nets(state, 'fb'))
