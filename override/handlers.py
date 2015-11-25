import config
import os

def boot(output, default):
    def handler(state):
        tmp = '{}.new'.format(output)
        with open(tmp, 'w') as out:
            print >> out, '#!ipxe\n'
            for host in state.hosts:
                if 'boot' in host.props:
                    print >> out, 'set default_{} {}'.format(
                        host.name, host.props['boot'])
            print >> out
            print >> out, \
                ('set default {}\n'.format(default) +
                 'set name ${hostname}.${domain}\n' +
                  'isset default_${name} && set default ${default_${name}}')
        os.rename(tmp, output)
    return handler

HANDLERS = [boot(config.BOOT, config.BOOT_DEFAULT)]
