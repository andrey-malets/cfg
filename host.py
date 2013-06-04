import re

from util import ValueFromGroup, primitive
import defaults

class Host:
    @staticmethod
    def expand_mac(mac):
        return '{}:{}:{}:{}:{}:{}'.format(mac[0:2], mac[2:4],  mac[4:6],
                                          mac[6:8], mac[8:10], mac[10:12])
    @staticmethod
    def get_type(name):
        for htype in ['ap', 'switch', 'ups', 'ipmi', 'amt']:
            if name.endswith('-%s' % htype): return htype
        return 'host'

    def __init__(self, data):
        default = defaults.get()
        names = data.pop(0)
        if type(names) == list:
            self.sname    = names[0]
            self.name     = default.expand_host(names.pop(0))
            self.aliases  = map(default.expand_host, names)
            self.saliases = names
        else:
            self.name    = default.expand_host(names)
            self.sname   = names
            self.aliases = []
            self.saliases = []

        self.htype = Host.get_type(self.sname)

        self.addr = default.expand_ip(data.pop(0)) if len(data) else None

        if len(data) and type(data[0]) is not dict:
            macs = data.pop(0)
            self.macs = (map(Host.expand_mac, macs)
                            if type(macs) == list
                            else [Host.expand_mac(macs)])
        else:
            self.macs = []

        self.props = data[0] if len(data) else {}

    def get_snames(self):
        return [self.sname] + self.saliases

    def get_props(self):
        return self.props

    def clean(self):
        def step(attr):
            if primitive(attr):
                return attr
            elif type(attr) == ValueFromGroup:
                return attr.value
            elif type(attr) == list:
                return map(step, attr)
            elif type(attr) == dict:
                for key in attr.iterkeys():
                    attr[key] = step(attr[key])
                return attr
            else:
                assert False, "unknown type %s" % type(attr)
        self.props = step(self.props)

    def get_name(self):
        return self.sname

    def __str__(self):
        return '{}: {}, aliases: {}, address: {}, macs: {}, props: {}'.format(
            self.htype, self.name, self.aliases, self.addr, self.macs, self.props)
    def __repr__(self):
        return '{} "{}"'.format(self.htype, self.sname)

def check_hosts(hosts):
    return fold_snames(hosts)

def fold_snames(hosts):
    names = {}
    errors = []
    for host in hosts:
        for sname in host.get_snames():
            if sname in names:
                errors.append(Exception('duplicate name %s' % sname))
            names[sname] = host
    return errors
