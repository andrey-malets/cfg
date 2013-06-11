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
        
    def __init__(self, data):
        addr, mask  = data.pop(0).split('/')
        self.addr   = Network.stoi(addr)
        self.count  = int(mask)
        self.mask   = -1 << (32-int(mask))
        self.router = Network.stoi(data.pop(0))
        self.props  = {} if not len(data) else data.pop(0)
        self.dhcp   = None if 'dhcp' not in self.props else self.props['dhcp'].split('-')
        assert (self.addr & ~self.mask) == 0, 'invalid network %s' % self
        assert self.router & self.mask == self.addr, 'invalid router for %s' % self

    def __str__(self):
        return '%s/%s' % (self.get_addr(), self.get_mask())

    def has(self, addr):
        return Network.stoi(addr) & self.mask == self.addr if addr else False

    def get_addr(self): return Network.itos(self.addr)

    def get_mask(self): return Network.itos(self.mask)

    def is_classful(self):
        return self.count % 8 == 0

    def get_router(self): return Network.itos(self.router)

    def get_dhcp(self):
        if not self.dhcp: return None
        addr = self.get_addr()
        base = addr[0:addr.rindex('.')]
        return ('%s.%s' % (base, self.dhcp[0]), '%s.%s' % (base, self.dhcp[1]))

def choose(nets, addr):
    candidates = filter(lambda net: net.get_addr().startswith(addr), nets)
    if len(candidates) == 1:
        return candidates[0]
    elif len(candidates) > 1:
        raise Exception('multiple networks chosen for %s, clarify' % addr)
    else:
        raise Exception('no networks chosen for %s' % addr)
