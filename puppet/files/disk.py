#!/usr/bin/env python

import argparse
import json
import os
import socket
import subprocess
import sys
import shutil
import tempfile
import urllib2

def get_property(config_url, prop):
    hostname = subprocess.check_output(['hostname', '-f']).strip()
    url = '{}/{}?{}'.format(config_url, hostname, prop)
    return json.load(urllib2.urlopen(url))

def get_pattern(config_url): return get_property(config_url, 'disk')
def get_layout(config_url): return get_property(config_url, 'disk_layout')

def find_disk(pattern):
    path = '/dev/disk/by-id/{}'.format(pattern)
    ndisks = int(subprocess.check_output(
        ['/bin/bash', '-c',
         'shopt -s nullglob; disks=({}); echo ${{#disks[@]}}'.format(path)]))
    if ndisks != 1:
        print >> sys.stderr, ('there must be exactly one disk with pattern {}, '
                              ' got {}, exiting.'.format(ndisks))
        sys.exit(1)
    return subprocess.check_output(
        ['/bin/bash', '-c', 'readlink -f {}'.format(path)]).strip()

def maybe_free_disk():
    proc = subprocess.Popen(['/bin/mountpoint', '/place'],
                            stdout=subprocess.PIPE)
    proc.communicate()
    if proc.returncode == 0:
        subprocess.check_call(['/bin/umount', '/place'])

def label_fs(device, fs, label):
    if fs == 'ntfs':
        cmd = ['ntfslabel', device, label]
    elif fs == 'ext2' or fs == 'ext3' or fs == 'ext4':
        cmd = ['tune2fs', '-L', label, device]
    else:
        raise ValueError('do not know how to label fs "{}"'.format(fs))
    subprocess.check_call(cmd)

def create(device, layout):
    def mb(pos): return '{}MB'.format(pos)

    parted_cmds = [['mklabel', 'gpt']]
    mkfs_cmds = []
    pos = 0
    for num, part in enumerate(layout):
        start = '0%' if not num else mb(pos)
        cmd = ['mkpart', 'primary']
        if 'size' in part:
            pos += int(part['size'])
            end = mb(pos)
        else:
            assert num == len(layout) - 1, \
                'only the last partition is allowed not to have size'
            end = '100%'
        if 'format' in part:
            fs = part['format']
            fs_label = part.get('fslabel')
            cmd.append(fs)
            mkfs_cmds.append((num, fs, fs_label))
        elif 'fs' in part:
            cmd.append(part['fs'])
        parted_cmds.append(cmd + [start, end])
        for flag in part.get('flags', []):
            parted_cmds.append(['set', str(num+1), flag, 'on'])
        if 'label' in part:
            parted_cmds.append(['name', str(num+1), part['label']])
    for cmd in parted_cmds:
        subprocess.check_call(['parted', '-s', device] + cmd)
    subprocess.check_call(['partprobe', device])
    subprocess.check_call(['udevadm', 'settle'])
    for num, fs, label in mkfs_cmds:
        opts = ['-f' if fs == 'ntfs' else '-F']
        fs_device = '{}{}'.format(device, num+1)
        subprocess.check_call(['mkfs.{}'.format(fs)] + opts + [fs_device])
        if label is not None:
            label_fs(fs_device, fs, label)

def get_boot(device, layout):
    for num, part in enumerate(layout):
        if part.get('label') == 'boot':
            return '{}{}'.format(device, num+1)

def write_grub_config(destination, layout):
    with open(destination, 'w') as output:
        output.write(
"""set menu_color_normal=cyan/blue
set menu_color_highlight=white/blue
set timeout=5

menuentry 'Network boot' {
    linux16 /ipxe.lkrn
}
""")
        for num, part in enumerate(layout):
            if 'boot' in part:
                boot = part['boot']
                boot_type = boot['type']
                if boot_type == 'cow':
                    template = """
menuentry 'Debian GNU/Linux ({description})' {{
    linux (hd0,gpt{num}){kernel} \
        root=/dev/mapper/root ro quiet cowtype={type} cowsrc=local
    initrd (hd0,gpt{num}){initrd}
}}
"""
                    for cow_type in [('', 'use current disk state, if possible'),
                                     ('clear', 'reset disk state'),
                                     ('mem', 'force memory session')]:
                        output.write(template.format(kernel=boot['kernel'],
                                                     initrd=boot['initrd'],
                                                     num=num+1,
                                                     type=cow_type[0],
                                                     description=cow_type[1]))
                elif boot_type == 'windows':
                    template = """
menuentry 'Windows' {{
    linux16 /memdisk harddisk
    initrd16 (hd0,gpt{num}){vhd}
}}
"""
                    output.write(template.format(num=num+1, vhd=boot['vhd']))

def configure(device, layout):
    boot = get_boot(device, layout)
    temp_dir = None
    try:
        temp_dir = tempfile.mkdtemp()
        subprocess.check_call(['mount', boot, temp_dir])
        subprocess.check_call(['grub-install', device,
                               '--boot-directory', temp_dir])
        shutil.copy2('/usr/lib/syslinux/memdisk', temp_dir)
        shutil.copy2('/var/lib/cfg/ipxe.lkrn', temp_dir)
        write_grub_config('{}/grub/grub.cfg'.format(temp_dir), layout)
    finally:
        if temp_dir:
            subprocess.call(['umount', temp_dir])
            os.rmdir(temp_dir)

def main(raw_args):
    parser = argparse.ArgumentParser(description='Configure local disk')
    parser.add_argument(
        '-c', help='config API url', default='https://urgu.org/config')
    args = parser.parse_args(raw_args)

    disk, layout = find_disk(get_pattern(args.c)), get_layout(args.c)

    maybe_free_disk()
    create(disk, layout)
    configure(disk, layout)

if __name__ == '__main__':
    main(sys.argv[1:])
