class Network:
    @staticmethod
    def stoi(addr):
        octets = map(int, addr.split('.'))
        octets.extend([0 for _ in range(4-len(octets))])
        fi, se, th, fo = octets
        return (fi << 24) | (se << 16) | (th << 8) | fo

    @staticmethod
    def itos(addr):
        octets = []
        for octet in range(4):
            octets.append('%d' % (addr & 0xff))
            addr = addr >> 8
        return '.'.join(reversed(octets))
        
    def __init__(self, data, router_attrs):
        addr, mask   = data.pop(0).split('/')
        self.addr    = Network.stoi(addr)
        self.count   = int(mask)
        self.mask    = -1 << (32-int(mask))
        self.router  = Network.stoi(data.pop(0))
        self.props   = {} if not len(data) else data.pop(0)
        self.iface   = router_attrs['dev'].get(str(self), None)
        self.nagios  = router_attrs['src'].get(str(self), None)
        self.dhcp    = None if 'dhcp' not in self.props else self.props['dhcp'].split('-')
        self.private = self.props.get('private', 0)
        assert (self.addr & ~self.mask) == 0, 'invalid network %s' % self
        assert self.router & self.mask == self.addr, 'invalid router for %s' % self
        assert self.is_classful() or 'rdns' not in self.props, ('rdns in classless net %s' %
            self.get_addr())

    def __str__(self):
        return '%s/%s' % (self.get_addr(), self.count)

    def has(self, addr):
        return Network.stoi(addr) & self.mask == self.addr if addr else False

    def get_addr(self): return Network.itos(self.addr)

    def get_mask(self): return Network.itos(self.mask)

    def is_classful(self):
        return self.count % 8 == 0

    def get_router(self): return Network.itos(self.router)

    def get_rdns_zone(self):
        assert self.is_classful(), 'the net should be classful'
        return '%s.in-addr.arpa' % '.'.join(reversed(
            self.get_addr().split('.')[0:(self.count / 8)]))

    def get_dhcp(self):
        if not self.dhcp: return None
        addr = self.get_addr()
        base = addr[0:addr.rindex('.')]
        return ('%s.%s' % (base, self.dhcp[0]), '%s.%s' % (base, self.dhcp[1]))

    def get_nagios(self):
        return self.nagios

def choose_net(nets, addr):
    candidates = filter(lambda net: net.get_addr().startswith(addr), nets)
    if len(candidates) == 1:
        return candidates[0]
    elif len(candidates) > 1:
        raise Exception('multiple networks chosen for %s, clarify' % addr)
    else:
        raise Exception('no networks chosen for %s' % addr)

def belongs_to(nets, host):
    if host.addr != None:
        candidates = filter(lambda net: net.has(host.addr), nets)
        assert len(candidates) < 2, 'overlapping networks'
        return candidates[0] if len(candidates) else None
    else:
        return None

def get_nagios(nets, addr):
    candidates = filter(lambda net: net.has(addr), nets)
    if len(candidates) == 1:
        return candidates[0].get_nagios()
    elif len(candidates) > 1:
        raise Exception('multiple networks chosen for %s, clarify' % addr)
    else:
        return None
