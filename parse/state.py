from defaults import Defaults
from host     import Host, check_hosts
from group    import Group, expand_groups
from network  import Network, belongs_to
from user     import User

import network
import yaml, json

def init_yaml_ruby_parsers():
    def construct_ruby_object(loader, suffix, node):
        return loader.construct_yaml_map(node)

    def construct_ruby_sym(loader, node):
        return loader.construct_yaml_str(node)

    yaml.add_multi_constructor(u"!ruby/object:", construct_ruby_object)
    yaml.add_constructor(u"!ruby/sym", construct_ruby_sym)

class BackupItem:
    def __init__(self, bhost, bprops, hour=None, minute=None):
        self.bhost, self.bprops = bhost, bprops
        self.hour, self.minute = hour, minute

class State:
    def __init__(self, config, router_attrs):
        self.errors = []
        self.defaults = Defaults(config['defaults'], self.errors)

        self.hosts    = map(lambda item: Host(item, self.defaults),
                                     config['hosts'])
        self.groups   = map(Group,   config['groups'])
        self.networks = map(lambda item: Network(item, router_attrs),
                                         config['networks'])

        def is_group(line): return len(line) == 2
        def is_user(line): return len(line) > 2

        people = config['people']
        self.users = dict((user.nickname, user) for user in
            map(User, filter(is_user, people)))
        self.user_groups = dict(filter(is_group, people))

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

    def is_user(self, spec):
        assert(spec in self.users or spec in self.user_groups)
        return spec in self.users

    def build_backup_schedule(self, host):
        from datetime import datetime, date, time, timedelta

        assert 'backups' in host.props
        fakedate = date(1970, 1, 1)
        starttime = time(3)
        btime = datetime.combine(fakedate, starttime)
        for bhost, bprops in host.props['backups'][1].iteritems():
            yield BackupItem(bhost, bprops, hour=btime.hour, minute=btime.minute)
            btime = btime + timedelta(minutes=10)
            # do not build too big schedule
            assert btime < datetime.combine(fakedate, time(7))

    def parse_facts(self, facts_path):
        init_yaml_ruby_parsers()
        for host in self.hosts:
            host.facts = None
            try:
                with open('%s/%s.yaml' % (facts_path, host.name)) as facts:
                    raw_facts = yaml.load(facts)
                    assert(raw_facts['name'] == host.name)
                    host.facts_expiration = raw_facts.get('expiration', None)
                    host.facts = raw_facts.get('values', {})
                    if 'pyxendomains' in host.facts:
                        host.facts['pyxendomains'] = json.loads(
                            host.facts['pyxendomains'])
                        for vm_name in host.facts['pyxendomains'].iterkeys():
                            vm = self.find(vm_name)
                            if vm != None:
                                vm.vm_host = host
            except Exception as e:
                pass # that's OK
