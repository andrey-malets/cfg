#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os, sys


PREFIX='/sys/class/hwmon'

def get_devices():
    rv = {}
    for comp in os.listdir(PREFIX):
        devpath = '%s/%s/device/' % (PREFIX, comp)
        namepath = '%s/name' % devpath
        if os.path.isfile(namepath):
            with open(namepath) as namefile:
                name = open(namepath).read().strip()
                rv[devpath] = name
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

def check_sensor(devpath, devname, name, values):
    senspath = '%s/%s_input' % (devpath, name)
    (cmin, wmin, wmax, cmax) = map(int, values.split(','))
    if not os.path.isfile(senspath):
        return (2, 'did not find %s for %s!' % (devname, name))
    value = None
    with open (senspath) as sensor:
        raw_value = sensor.read()
        value = normalize_value(name, raw_value)
        if value == None:
            return (2, 'cant normalize value "%s"' % raw_value)
    assert(value)
    formatted_value = '%s:%s: %s' % (devname, name, format_value(name, value))
    status = 0
    if value < cmin or value > cmax:
        status = 2
    elif value < wmin or value > wmax:
        status = 1
    return (status, formatted_value)

if __name__ == '__main__':
    if len(sys.argv) != 2 or len(sys.argv[0]) == 0:
        print 'CRITITAL: could not parse command line'
        sys.exit(2)

    matching = {}
    specs = sys.argv[1].split('+')
    for spec in specs:
        try:
            devname, sensorname, values = spec.split(':')
            sensors = matching.get(devname, [])
            sensors.append((sensorname, values))
            matching[devname] = sensors
        except:
            print 'CRITITAL: could not parse command line'
            sys.exit(2)

    results = [[], [], []]
    all_status = 0

    for devpath, name in get_devices().iteritems():
        if name in matching:
            for sensorname, values in matching[name]:
                status, message = check_sensor(devpath, name, sensorname, values)
                results[status].append(message)
                all_status = max(all_status, status)

    messages = ['OK', 'WARNING', 'CRITICAL']
    print 'Sensors %s: %s' % (messages[all_status], ', '.join(results[all_status]))
    sys.exit(all_status)
