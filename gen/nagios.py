import jinja2
from cmd import add_cmd

@add_cmd('nagios', True, 0)
def gen(state, template):
    return jinja2.Template(template).render(state=state)
