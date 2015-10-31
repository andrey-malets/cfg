#!/usr/bin/env python

import glob, json, os, re

def get_name(filename):
    return re.match('(.+)\.cfg', os.path.basename(filename)).group(1)

def get_raw_config(filename):
    try:
        raw_config = {}
        with open(filename) as fd:
            exec(fd.read(), raw_config)
        return raw_config
    except:
        return None

def filter_config(raw_config):
    keys = ['name',
            'memory',
            'disk',
            'boot',
            'vif',
            'cpus',
            'vnclisten',
            'localtime']
    rv = {}
    for key in keys:
        rv[key] = raw_config.get(key, None)
    return rv

if __name__ == '__main__':
    filenames = glob.glob('/root/xen/*.cfg')
    configs = {}
    for filename in filenames:
        configs[get_name(filename)] = filter_config(get_raw_config(filename))
    print json.dumps(configs)
