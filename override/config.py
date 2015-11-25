import os.path

CFG = os.path.join(os.path.dirname(__file__), os.path.pardir,
                   'cfg', 'conf.yaml')

WEB_PATH = '/config'

DB = '/var/lib/cfg/overrides.json'

ACL = ['d', 'pioneer']

BOOT = '/var/www/urgu.org/boot'
BOOT_DEFAULT = 'local'
