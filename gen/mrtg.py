import jinja2
from cmd import add_cmd

@add_cmd('ups_mrtg', True, 0)
def gen_ups_mrtg(state, template):
    return jinja2.Template(template).render(state=state)
