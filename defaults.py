import re
from util import ValidationError

class Defaults:
    _instance = None

    def __init__(self, data, errors):
        def check(data, item, descr):
            if not item in data:
                errors.append(ValidationError('no %s' % descr))
            else:
                return data[item]

        self.network_prefix = check(data, 'network_prefix', 'default network prefix')

        self.domains = {}
        self.def_domain = None

        for key, value in check(data, 'domains', 'domain substitution rules').iteritems():
            if key == 'default':
                self.def_domain = value
            else:
                for oldkey in self.domains.iterkeys():
                    if key.endswith(oldkey) or oldkey.endswith(key):
                        errors.append(ValidationError('two keys in domain defaults config have ' +
                            ('common suffix: %s and %s' % (key, oldkey))))
                self.domains[key] = value

        if not self.def_domain:
            errors.append(ValidationError('no default domain configured'))

    def expand_host(self, host):
        if '.' in host:
            for patt, subst in self.domains.iteritems():
                if host.endswith(patt):
                    return host[0:host.rindex(patt)] + subst
            return host

        return '%s.%s' % (host, self.def_domain)

    def expand_ip(self, ip):
        return ('%s.%s' % (self.network_prefix, ip)
                if not re.match('^\d+\.\d+\.\d+\.\d+$', str(ip))
                else ip)

def init(data):
    errors = []
    Defaults._instance = Defaults(data, errors)
    return errors

def get():
    if Defaults._instance:
        return Defaults._instance
    else:
        raise Exception('no defaults configured')
