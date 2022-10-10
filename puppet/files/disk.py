#!/usr/bin/env python3

import argparse
import glob
import json
import logging
import os
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.error
import urllib.parse
import urllib.request


def get_property(config_url, prop):
    hostname_output = subprocess.check_output(['hostname', '-f'], text=True)
    hostname = hostname_output.strip().lower()
    url = '{}/{}?{}'.format(config_url, hostname, prop)
    logging.info('Getting %s property from %s', prop, url)
    return json.load(urllib.request.urlopen(url))


def get_pattern(config_url):
    return get_property(config_url, 'disk')


def get_layout(config_url):
    return get_property(config_url, 'disk_layout')


def read_links(path):
    while os.path.islink(path):
        old_path = path
        full_path = os.path.join(os.path.dirname(path), os.readlink(path))
        path = os.path.normpath(full_path)
        logging.debug('Resolved %s to %s', old_path, path)
    return path


def find_disk(pattern):
    full_pattern = '/dev/disk/by-id/{}'.format(pattern)
    logging.debug('Trying to find disk by pattern: %s', full_pattern)
    paths = glob.glob(full_pattern)
    if len(paths) != 1:
        logging.error('there must be exactly one disk with pattern %s, '
                      ' got %s, exiting.', full_pattern, len(paths))
        sys.exit(1)
    return paths[0]


def dmsetup_used_devices():
    device_num_re = re.compile(r'.*\((\d+):(\d+)\).*')
    dmsetup_ls_cmd = ['dmsetup', 'ls', '--tree', '-o', 'ascii']
    dmsetup_ls_output = subprocess.check_output(dmsetup_ls_cmd, text=True)
    for line in dmsetup_ls_output.splitlines():
        match = device_num_re.match(line)
        assert match, ('Did not parse device number from dmsetup '
                       'output line: {}'.format(line))
        yield int(match.group(1)), int(match.group(2))


def check_unused_by_dmsetup(disk):
    partitions = glob.glob('{}*'.format(disk))
    if not partitions:
        logging.info('Disk %s has no partitions', disk)
        return

    used = list(dmsetup_used_devices())
    logging.info('Devices used by dmsetup: %s', used)
    for partition in partitions:
        part_stat = os.stat(partition)
        major, minor = os.major(part_stat.st_rdev), os.minor(part_stat.st_rdev)
        if (major, minor) in used:
            logging.error('%s is used by dmsetup, cannot continue!', partition)
            sys.exit(1)


def maybe_free_place():
    logging.debug('Checking if /place needs to be unmounted')
    proc = subprocess.Popen(['/bin/mountpoint', '/place'],
                            stdout=subprocess.PIPE)
    proc.communicate()
    if proc.returncode == 0:
        logging.info('Unmounting /place')
        subprocess.check_call(['/bin/umount', '/place'])


def label_fs(device, fs, label):
    if fs == 'ntfs':
        cmd = ['ntfslabel', device, label]
    elif fs == 'ext2' or fs == 'ext3' or fs == 'ext4':
        cmd = ['tune2fs', '-L', label, device]
    elif fs == 'fat32':
        pass  # skip since this is not useful anyway
    else:
        raise ValueError('do not know how to label fs "{}"'.format(fs))
    logging.info('Running label fs cmd: %s', cmd)
    subprocess.check_call(cmd)


def get_mkfs_cmd(fs):
    if fs == 'fat32':
        return ['mkfs.fat', '-F', '32']
    elif fs == 'ntfs':
        return ['mkfs.ntfs', '-f']
    elif fs == 'hfs':
        return ['mkfs.hfs']
    else:
        return ['mkfs.{}'.format(fs), '-F']


def partition_device(disk_device, number):
    return '{}{}'.format(disk_device, number + 1)


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
            parted_cmds.append(['name', str(num+1),
                                "'{}'".format(part['label'])])
    for cmd in parted_cmds:
        full_cmd = ['parted', '-s', device] + cmd
        logging.info('Running parted cmd: %s', full_cmd)
        subprocess.check_call(full_cmd)
    logging.info('Refreshing partition map with partprobe')
    subprocess.check_call(['partprobe', device])
    logging.info('Waiting for partitions to appear with "udevadm settle"')
    subprocess.check_call(['udevadm', 'settle'])
    for num, fs, label in mkfs_cmds:
        fs_device = partition_device(device, num)
        cmd = get_mkfs_cmd(fs) + [fs_device]
        logging.info('Running mkfs cmd: %s', cmd)
        subprocess.check_call(cmd)
        if label is not None:
            label_fs(fs_device, fs, label)


def get_boot(device, layout):
    for num, part in enumerate(layout):
        if part.get('label') == 'boot':
            return partition_device(device, num)


def write_grub_config(destination, layout):
    with open(destination, 'w') as output:
        output.write(
            """set menu_color_normal=cyan/blue
set menu_color_highlight=white/blue
set timeout=5

menuentry 'Network boot' {
    linux16 /ipxe.lkrn
}
"""
        )
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
                    for cow_type in [
                            ('', 'use current disk state, if possible'),
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
                elif boot_type == 'macos':
                    template = """
menuentry '' {{
    chainloader (hd0,gpt{num}){bootsector}
}}
"""
                    output.write(template.format(
                        num=num+1, bootsector=boot['bootsector']))


def configure(device, layout):
    boot = get_boot(device, layout)
    logging.info('Boot partition is %s', boot)
    temp_dir = None
    try:
        logging.info('Installing and configuring GRUB')
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
    parser.add_argument('-c', metavar='URL', help='config API url',
                        default='https://urgu.org/config')
    parser.add_argument('-d', metavar='DEV', help='Specify disk explicitly')
    parser.add_argument('-s', action='store_true',
                        help='Skip bootloader configuration')
    parser.add_argument('-v', action='store_true', help='Be verbose')
    args = parser.parse_args(raw_args)

    logging.basicConfig(level=logging.DEBUG if args.v else logging.WARNING)

    if args.d:
        disk_path = args.d
        logging.info('Using explicit disk path: %s', disk_path)
    else:
        pattern = get_pattern(args.c)
        logging.info('Disk pattern: %s', pattern)
        disk_path = find_disk(pattern)
        logging.info('Found disk path: %s', disk_path)

    disk = read_links(disk_path)

    layout = get_layout(args.c)
    logging.info('Disk layout: %s', json.dumps(layout, indent=2))

    maybe_free_place()
    check_unused_by_dmsetup(disk)

    create(disk, layout)
    if not args.s:
        configure(disk, layout)


if __name__ == '__main__':
    main(sys.argv[1:])
