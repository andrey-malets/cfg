import backup
import defaults
import group
import host
import json
import network
import os.path
import user
import util
import yaml

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


class Encoder(json.JSONEncoder):

    def __init__(self, *args, **kwargs):
        super(Encoder, self).__init__(*args, **kwargs)

    def default(self, obj):
        if type(obj) is util.ValueFromGroup:
            return obj.value
        elif type(obj) is group.Group:
            return obj.name
        else:
            return super(Encoder, self).default(obj)


class Overrides:
    HOSTS_KEY = 'hosts'
    GROUPS_KEY = 'groups'

    def __init__(self, hosts, groups):
        self.hosts = hosts
        self.groups = groups

    @staticmethod
    def load(filename):
        rv = Overrides({}, {})
        if os.path.exists(filename):
            with open(filename) as db:
                state = json.load(db)
                rv.hosts = state.get(Overrides.HOSTS_KEY, {})
                rv.groups = state.get(Overrides.GROUPS_KEY, {})
        return rv

    def save(self, filename):
        with open(filename, 'w') as db:
            json.dump({Overrides.HOSTS_KEY: self.hosts,
                       Overrides.GROUPS_KEY: self.groups}, db, indent=2)
            print >> db

    def get(self, entity):
        collection = self.hosts if type(entity) is host.Host else self.groups
        if entity.name not in collection:
            collection[entity.name] = {}
        return collection[entity.name]

    @staticmethod
    def apply_props(src, dst):
        assert type(src) is dict and type(dst) is dict
        for key, value in src.iteritems():
            assert not key in dst or type(src[key]) == type(dst[key])
            if type(src[key]) is dict:
                dst[key] = apply_props(src[key], dst[key])
            else:
                dst[key] = src[key]
        return dst

    @staticmethod
    def do_apply(items, finder):
        for item, props in items.iteritems():
            entity = finder(item)
            if entity is not None:
                Overrides.apply_props(props, entity.props)

    def apply(self, state):
        Overrides.do_apply(self.hosts, state.find)
        Overrides.do_apply(self.groups, state.find_group)


class State:
    def __init__(self, config, router_attrs=None, overrides=None):
        self.errors = []
        self.defaults = defaults.Defaults(config['defaults'], self.errors)

        self.hosts    = map(lambda item: host.Host(item, self.defaults),
                            config['hosts'])
        self.groups   = map(group.Group, config['groups'])
        self.group_by_name = dict(map(lambda group: (group.name, group),
                                      self.groups))
        self.networks = map(lambda item: network.Network(item, router_attrs),
                                         config['networks'])
        self.backup_schedule = None

        def is_group(line): return len(line) == 2
        def is_user(line): return len(line) > 2

        people = config['people']
        self.users = dict((user.nickname, user) for user in
            map(user.User, filter(is_user, people)))
        self.user_groups = dict(filter(is_group, people))

        if overrides is not None:
            overrides.apply(self)

        self.errors.extend(host.check_hosts(self.hosts))
        self.errors.extend(group.expand_groups(self.groups, self.hosts))

        map(host.Host.clean, self.hosts)

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
        return network.belongs_to(self.networks, host)

    def find(self, hostname):
        candidates = filter(lambda host: (hostname in [host.name, host.sname]
            + host.aliases + host.saliases), self.hosts)
        return candidates[0] if len(candidates) == 1 else None

    def find_group(self, groupname):
        return self.group_by_name.get(groupname)

    def find_entity(self, name):
        maybe_host, maybe_group = self.find(name), self.find_group(name)
        return maybe_host if maybe_host else maybe_group

    def is_gray(self, host):
        return host.addr != None and host.addr.startswith(self.defaults.network_prefix)

    def is_user(self, spec):
        assert(spec in self.users or spec in self.user_groups)
        return spec in self.users

    def build_backup_schedule(self):
        self.backup_schedule = backup.build_schedule(self)

    def get_backup_schedule(self, host):
        if self.backup_schedule == None:
            self.build_backup_schedule()
        return self.backup_schedule[host]

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
