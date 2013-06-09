from cmd import add_cmd

@add_cmd('list_nets', False, 0)
def list_nets(state):
    return '\n'.join(map(lambda net: net.get_addr(), state.networks))
