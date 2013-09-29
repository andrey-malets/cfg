import jinja2
from cmd import add_cmd

@add_cmd('ext_http', True, 0)
def gen_ext_http(state, template):
    return jinja2.Template(template).render(state=state)
