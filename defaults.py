import re

class Defaults:
    _instance = None

    @staticmethod
    def check(data, item, descr):
        if not item in data:
            raise Exception('no %s' % descr)
        else:
            return data[item]

    def __init__(self, data):
        self.network_prefix = self.check(data, 'network_prefix', 'default network prefix')

        self.domains = {}
        self.def_domain = None

        for key, value in self.check(data, 'domains', 'domain substitution rules').iteritems():
            if key == 'default': self.def_domain = value
            else: self.domains[key] = value

    def expand_host(self, host):
        if '.' in host:
            for patt, subst in self.domains.iteritems():
                if host.endswith(patt):
                    return host[0:host.rindex(patt)] + subst
            return host

        elif self.def_domain:
            return '%s.%s' % (host, self.def_domain)
        else:
            raise Exception(("""host "%s" with default domain but""" +
                             """no default domain configured""") % host)

    def expand_ip(self, ip):
        return ('%s.%s' % (self.network_prefix, ip)
                if not re.match('^\d+\.\d+\.\d+\.\d+$', str(ip))
                else ip)

def init(data):
    Defaults._instance = Defaults(data)

def get():
    if Defaults._instance:
        return Defaults._instance
    else:
        raise Exception('no defaults configured')
