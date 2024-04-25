import os.path

WEB_PATH = '/config'
ACL = [
    'd',
    'h', 'hamming',
    'r', 'ritchie',
]

CFG = os.path.join(os.path.dirname(__file__), os.path.pardir,
                   'cfg', 'conf.yaml')
DB = '/var/lib/cfg/overrides.json'
LOCK = '/var/lib/cfg/overrides.lock'

BOOT = '/var/www/urgu.org/boot'
BOOT_DEFAULT = 'local'
