import util

class Host(object):
    @staticmethod
    def expand_mac(mac):
        return '{0}:{1}:{2}:{3}:{4}:{5}'.format(mac[0:2], mac[2:4],  mac[4:6],
                                                mac[6:8], mac[8:10], mac[10:12])
    def __init__(self, data, defaults):
        names = data.pop(0)
        names = [names] if type(names) == str else names
        self.sname, self.name = defaults.expand_host(names[0])
        assert len(self.name) and len (self.sname)
        self.saliases = []
        self.aliases = []
        for raw_alias in names[1:]:
            salias, alias = defaults.expand_host(raw_alias)
            if len(salias): self.saliases.append(salias)
            if len(alias): self.aliases.append(alias)

        self.snames = [self.sname] + self.saliases

        self.nick  = reduce(lambda cur, x: cur if len(cur) < len(x) else x,
                            [self.sname] + self.saliases)

        self.addr  = (defaults.expand_ip(data.pop(0))
            if (len(data) and type(data[0]) is not dict) else None)

        if len(data) and type(data[0]) is not dict:
            macs = data.pop(0)
            self.macs = (map(Host.expand_mac, macs)
                            if type(macs) == list
                            else [Host.expand_mac(macs)])
        else:
            self.macs = []

        self.props = data[0] if len(data) else {}

        self.admin = self.props.get('admin', None)

        self.fb = map(defaults.expand_ip, self.props.get('fb', []))

        self.groups = []
        self.vm_host = None

    @property
    def services(self):
        return self.props.get('services', [])

    def clean(self):
        def step(attr):
            if util.is_primitive(attr) or util.is_from_group(attr):
                return util.get_value(attr)
            elif type(attr) == list:
                return map(step, attr)
            elif type(attr) == dict:
                for key in attr.iterkeys():
                    attr[key] = step(attr[key])
                return attr
            else:
                assert False, "unknown type %s" % type(attr)
        self.props = step(self.props)

    def __str__(self):
        return self.name

    def format(self):
        return 'host {0}, aliases: {1}, address: {2}, macs: {3}, props: {4}'.format(
            self.name, self.aliases, self.addr, self.macs, self.props)

def check_hosts(hosts):
    names = set()
    dups = set(name for host in hosts for name in [host.name] + host.aliases
        if name in names or names.add(name))
    return map(lambda name: Exception('duplicate name %s' % name), dups)

def get_sname_dups(hosts):
    sname_to_host = dict()
    for host in hosts:
        for name in host.snames:
            names = sname_to_host.get(name, [])
            names.append(host.name)
            sname_to_host[name] = names

    dups = set()
    for names in sname_to_host.itervalues():
        if len(names) > 1:
            dups.update(names)

    return dups
