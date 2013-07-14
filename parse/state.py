from defaults import Defaults
from host     import Host, check_hosts
from group    import Group, expand_groups
from network  import Network, belongs_to
from user     import User

import network

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
        return network.choose_net(self.networks, net_name)

    def get_canonical_hostname(self, host):
        return self.defaults.get_canonical_hostname(host.name)

    def get_nagios(self, addr):
        rv = self.defaults.nagios
        if addr:
            chosen = network.get_nagios(self.networks, addr)
            if chosen:
                rv = chosen
        return self.defaults.expand_ip(rv)

    def belongs_to(self, host):
        return belongs_to(self.networks, host)

    def is_gray(self, host):
        return host.addr != None and host.addr.startswith(self.defaults.network_prefix)
