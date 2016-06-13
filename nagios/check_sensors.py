#!/usr/bin/env python
# -*- coding: utf-8 -*-

import collections, glob, itertools, os, re, sys

def get_devices():
    PREFIX='/sys/class/hwmon'
    rv = collections.defaultdict(list)
    for comp in os.listdir(PREFIX):
        basepath = '%s/%s' % (PREFIX, comp)
        for devpath in (basepath, '%s/device' % basepath):
            namepath = '%s/name' % devpath
            if os.path.isfile(namepath):
                with open(namepath) as namefile:
                    name = open(namepath).read().strip()
                    rv[name].append(devpath)
    return rv

def normalize_value(name, raw_value):
    if name.startswith('in'):
        # millivolts
        return float(raw_value) / 1000
    elif name.startswith('fan'):
        # RPM
        return int(raw_value)
    elif name.startswith('temp'):
        # millidegree
        return float(raw_value) / 1000
    else:
        return None

def format_value(name, value):
    rules = {'in': '%f V', 'fan': '%d RPM', 'temp': '%.1f C'}
    for prefix, fmt in rules.iteritems():
        if name.startswith(prefix):
            return fmt % value
    assert(False)

def check_sensor(devname, devpaths, patt, values):
    senspatts = ['%s/%s_input' % (devpath, patt) for devpath in devpaths]
    (cmin, wmin, wmax, cmax) = map(int, values.split(','))

    sensors = sum([glob.glob(senspatt) or [] for senspatt in senspatts], [])
    if len(sensors) == 0:
        return [(2, 'no sensors found matching %s:%s!' % (devname, patt))]
    results = []
    for senspath in sensors:
        assert(os.path.isfile(senspath))
        value = None
        with open (senspath) as sensor:
            raw_value = sensor.read().strip()
            value = normalize_value(patt, raw_value)
            if value == None:
                results.append((2, 'cant normalize value "%s"' % raw_value))
                continue
        assert(value)
        name = re.match('(.+)_input', os.path.basename(senspath)).group(1)
        formatted_value = '%s:%s: %s' % (devname, name, format_value(patt, value))
        status = 0
        if value < cmin or value > cmax:
            status = 2
        elif value < wmin or value > wmax:
            status = 1
        results.append((status, formatted_value))
    return results

if __name__ == '__main__':
    if len(sys.argv) != 2 or len(sys.argv[0]) == 0:
        print 'CRITITAL: could not parse command line'
        sys.exit(2)

    matching = {}
    specs = sys.argv[1].split('+')
    for spec in specs:
        try:
            devname, patt, values = spec.split(':')
            sensors = matching.get(devname, [])
            sensors.append((patt, values))
            matching[devname] = sensors
        except:
            print 'CRITITAL: could not parse command line'
            sys.exit(2)

    results = [[], [], []]
    all_status = 0

    for name, devpaths in get_devices().iteritems():
        if name in matching:
            for patt, values in matching[name]:
                for status, message in check_sensor(name, devpaths, patt, values):
                    results[status].append(message)
                    all_status = max(all_status, status)

    messages = ['OK', 'WARNING', 'CRITICAL']
    print 'Sensors %s: %s' % (messages[all_status], ', '.join(results[all_status]))
    sys.exit(all_status)
