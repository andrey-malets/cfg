#!/opt/local/bin/python2.7

import json, sys, yaml, re, copy

import dhcp, dns, iptables

from host    import Host, check_hosts
from group   import Group, expand_groups
from network import Network

if __name__ == '__main__':
    cfg = yaml.load(sys.stdin)
    hosts    = map(lambda data: Host(data),    cfg['hosts'])
    networks = map(lambda data: Network(data), cfg['networks'])
    groups   = map(lambda data: Group(data),   cfg['groups'] if 'groups' in cfg else [])
    users    = cfg['users'] if 'users' in cfg else []

    errors = []
    errors.extend(check_hosts(hosts))
    errors.extend(expand_groups(groups, hosts))
    for host in hosts: host.clean()

    if len(errors):
        for error in errors: print 'Error: %s' % error
        sys.exit(1)
    else:
        with open('dhcp.template', 'r') as dhcpt:
            template = dhcpt.read()
        print dhcp.gen(hosts, networks, template)
        #with open('urgu.org.template', 'r') as dnst:
        #    template = dnst.read()
        #print dns.gen_fwd(hosts, 'urgu.org', template)
        #print ''.join(iptables.gen_ports(hosts, '194.226.244.126', 'server'))
        #print dns.gen_fwd(hosts, 'urgu.org')
        #for host in hosts: print host
        #for network in networks: print network; print network.get_dhcp()
