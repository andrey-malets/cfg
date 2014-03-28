from defaults import Defaults
from host     import Host, check_hosts
from group    import Group, expand_groups
from network  import Network, belongs_to
from user     import User

import network

class State:
    def __init__(self, config, router_attrs):
        self.errors = []
        self.defaults = Defaults(config['defaults'], self.errors)

        self.hosts    = map(lambda item: Host(item, self.defaults),
                                     config['hosts'])
        self.groups   = map(Group,   config['groups'])
        self.networks = map(lambda item: Network(item, router_attrs),
                                         config['networks'])
        self.users    = dict((user.nickname, user) for user in
                            map(User, config['people']))

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

    def find(self, hostname):
        candidates = filter(lambda host: (hostname in [host.name, host.sname]
            + host.aliases + host.saliases), self.hosts)
        return candidates[0] if len(candidates) == 1 else None

    def is_gray(self, host):
        return host.addr != None and host.addr.startswith(self.defaults.network_prefix)
