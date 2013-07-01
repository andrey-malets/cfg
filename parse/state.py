from defaults import Defaults
from host     import Host, check_hosts
from group    import Group, expand_groups
from network  import Network, choose
from user     import User

class State:
    def __init__(self, config):
        self.errors = []
        self.defaults = Defaults(config['defaults'], self.errors)

        self.hosts    = map(lambda item: Host(item, self.defaults),
                                     config['hosts'])
        self.groups   = map(Group,   config['groups'])
        self.networks = map(Network, config['networks'])

        self.users    = map(User, config['people'])
        self.default_user = self.users[0] if len(self.users) else None

        self.errors.extend(check_hosts(self.hosts))
        self.errors.extend(expand_groups(self.groups, self.hosts))

        map(Host.clean, self.hosts)

    def choose_net(self, net_name):
        return choose(self.networks, net_name)
