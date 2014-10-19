import sys

def init(table, chain):
    print ('if iptables -t %s -L %s 2>/dev/null >/dev/null; '
        'then iptables -t %s -F %s; '
        'else iptables -t %s -N %s; fi' % ((table, chain) * 3))

def cn2chain(cn):
    return 'openvpn_%s' % cn

def ipp2src(ipp_ip):
    octets = ipp_ip.split('.')
    octets[3] = str(int(octets[3]) + 2)
    return '.'.join(octets)

def gen_user_chains(ipp_name, iface, target):
    users = {}
    aliases = {}
    with open(ipp_name, 'r') as ipp:
        for line in ipp:
            user, ip = line.strip().split(',')
            if not user in users:
                users[user] = []
            users[user].append(ipp2src(ip))
    for user in users:
        chain = cn2chain(user)
        init('filter', chain)
        for ip in users[user]:
            print ('iptables -A %s -i %s -s %s -p tcp -m state --state NEW '
                '-j %s' % (chain, iface, ip, target))
            print ('iptables -A %s -i %s -s %s -p udp -m state --state NEW '
                '-j %s' % (chain, iface, ip, target))

if __name__ == '__main__':
    gen_user_chains(*sys.argv[1:])
