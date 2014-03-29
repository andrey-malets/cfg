#!/usr/bin/env python

import os, re, sys, urllib2, urllib
from cookielib import CookieJar

def get_pwds():
    pwdfn = os.path.dirname(sys.argv[0]) + '/../cfg/pwds'
    with open(pwdfn, 'r') as pwdfile:
        for line in pwdfile:
            host, login, pwd = line.strip().split(':', 3)
            yield host, (login, pwd)

def get_ss_macs(host, login, pwd):
    def read(fd):
        return ''.join(fd)

    url_opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(CookieJar()))
    data = read(url_opener.open('http://%s/Web' % host,
        urllib.urlencode({'user_name' : login, 'password' : pwd, 'lang' : '0'})))

    #<input type=hidden name=uid id=uid value="ab000000" />
    uid = re.search('<input type=hidden name=uid id=uid value="(.+?)" />', data).group(1)
    data = read(url_opener.open(
        'http://%s/wcn/mac/summary_detail?uid=%s&ifname=&state=7' % (host, uid)))
    try:
        data = re.search('<pre id=mac16k.+?>(.+)</pre>', data, re.S).group(1).replace('\0','')
        # 00c0-b759-8b9d  1         Learned        Ten-GigabitEthernet1/1/1 AGING
        for line in data.split('\n'):
            match = re.search('^([0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4})\s+'
                              '(\d+)\s+(.+?)\s+(.+?)(\d+)\/(\d+)\/(\d+)\s+(\w+)\s+$', line)
            mac, vlan, state, ptype, unit, adap, port, aging = match.group(1,2,3,4,5,6,7,8)
            mac = mac.replace('-','')
            yield (mac, vlan), (state, "%s/%s/%s/%s" % (ptype, unit, adap, port))
    finally:
        data = read(url_opener.open('http://%s/wcn/logout?uid=%s' % (host, uid)))

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print >> sys.stderr, "usage: %s <host>" % sys.argv[0]
        sys.exit(1)
    host = sys.argv[1]
    pwds = dict(get_pwds())
    if not host in pwds:
        print >> sys.stderr, "no credentials for %s" % host
        sys.exit(2)
    login, pwd = pwds[host]
    table = dict(get_ss_macs(host, login, pwd))
    for (mac, vlan), (state, portspec) in table.iteritems():
        print "%s:%s,%s,%s" % (mac, vlan, state, portspec)
