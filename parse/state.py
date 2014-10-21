from defaults import Defaults
from host     import Host, check_hosts
from group    import Group, expand_groups
from network  import Network, belongs_to
from user     import User

import network
import yaml

def init_yaml_ruby_parsers():
    def construct_ruby_object(loader, suffix, node):
        return loader.construct_yaml_map(node)

    def construct_ruby_sym(loader, node):
        return loader.construct_yaml_str(node)

    yaml.add_multi_constructor(u"!ruby/object:", construct_ruby_object)
    yaml.add_constructor(u"!ruby/sym", construct_ruby_sym)

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

    def parse_facts(self, facts_path):
        init_yaml_ruby_parsers()
        for host in self.hosts:
            try:
                with open('%s/%s.yaml' % (facts_path, host.name)) as facts:
                    raw_facts = yaml.load(facts)
                    assert(raw_facts['name'] == host.name)
                    host.facts_expiration = raw_facts.get('expiration', None)
                    host.facts = raw_facts.get('values', {})
            except Exception as e:
                pass # that's OK
