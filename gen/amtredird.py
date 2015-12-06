import jinja2
from cmd import add_cmd

@add_cmd('amtredird', True, 2)
def gen_dhcp(state, template, passwd, images_path):
    with open(passwd) as passwdfile:
        default_user, default_passwd = passwdfile.read().strip().split(':', 1)

    def get_matching(state):
        return dict(map(lambda host: (state.find(host.props['amt']).name, host.name),
                    filter(lambda host: 'amt' in host.props, state.hosts)))

    return jinja2.Template(template).render(
        default_user=default_user, default_passwd=default_passwd,
        hosts=get_matching(state), images_path=images_path)
