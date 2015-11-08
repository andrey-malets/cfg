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

def get_config():
    CONFIG_URL = 'https://urgu.org/disk.json'
    hostname = subprocess.check_output(['hostname', '-f']).strip()
    return json.load(urllib2.urlopen(CONFIG_URL))[hostname]

def create(config, device):
    def mb(pos): return '{}MB'.format(pos)

    parted_cmds = [['mklabel', 'gpt']]
    mkfs_cmds = []
    pos = 0
    for num, part in enumerate(config):
        start = '0%' if not num else mb(pos)
        cmd = ['mkpart', 'primary']
        if 'size' in part:
            pos += int(part['size'])
            end = mb(pos)
        else:
            assert num == len(config) - 1, \
                'only the last partition is allowed not to have size'
            end = '100%'
        if 'format' in part:
            fs = part['format']
            cmd.append(fs)
            mkfs_cmds.append((num, fs))
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
    for num, fs in mkfs_cmds:
        subprocess.check_call(
            ['mkfs.{}'.format(fs), '-F', '{}{}'.format(device, num+1)])

def get_boot(config, device):
    for num, part in enumerate(config):
        if part.get('label') == 'boot':
            return '{}{}'.format(device, num+1)

def write_grub_config(config, destination):
    with open(destination, 'w') as output:
        output.write("""
set menu_color_normal=cyan/blue
set menu_color_highlight=white/blue
set timeout=5
""")
        for num, part in enumerate(config):
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

def configure(config, device):
    boot = get_boot(config, device)
    temp_dir = None
    try:
        temp_dir = tempfile.mkdtemp()
        subprocess.check_call(['mount', boot, temp_dir])
        subprocess.check_call(['grub-install', device,
                               '--boot-directory', temp_dir])
        shutil.copy2('/usr/lib/syslinux/memdisk', temp_dir)
        write_grub_config(config, '{}/grub/grub.cfg'.format(temp_dir))
    finally:
        if temp_dir:
            subprocess.call(['umount', temp_dir])
            os.rmdir(temp_dir)

def verify(config, device):
    raise NotImplementedError()

def main(raw_args):
    cmds = {'create': create, 'configure': configure, 'verify': verify}
    parser = argparse.ArgumentParser(
        description='Configure and verify disk state')
    parser.add_argument('COMMAND', help='command', choices = cmds.keys())
    parser.add_argument('DEVICE', help='device to operate on')

    args = parser.parse_args(raw_args)
    cmd = cmds[args.COMMAND]

    return cmd(get_config(), args.DEVICE)

if __name__ == '__main__':
    main(sys.argv[1:])
