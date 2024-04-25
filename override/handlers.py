import config
import os

def boot(output, default):
    def handler(state):
        tmp = '{}.new'.format(output)
        with open(tmp, 'w') as out:
            print('#!ipxe\n', file=out)
            for host in state.hosts:
                if 'boot' in host.props:
                    print('set default_{} {}'.format(
                        host.name, host.props['boot']), file=out)
                if 'console' in host.props:
                    print('set console_{} {}'.format(
                        host.name, host.props['console']), file=out)
            print(f"""
set name ${{hostname}}.${{domain}}

set default {default}
isset ${{default_${{name}}}} && set default ${{default_${{name}}}} ||

set console
isset ${{console_${{name}}}} && set console console=${{console_${{name}}}} ||""", file=out)
        os.rename(tmp, output)
    return handler

HANDLERS = [boot(config.BOOT, config.BOOT_DEFAULT)]
