import jinja2
from cmd import add_cmd

@add_cmd('ext_http', True, 1)
def gen_ext_http(state, template, keypath):
    return jinja2.Template(template).render(state=state, keypath=keypath)

@add_cmd('http_back', True, 1)
def gen_http_back(state, template, keypath):
    return jinja2.Template(template).render(state=state, keypath=keypath)

@add_cmd('https', False, 0)
def list_https_hosts(state):
    rv = []
    for host in state.hosts:
        if 'http' in host.services and state.belongs_to(host).private:
            rv.append('%s,%s.e.urgu.org' % (host.name, host.nick))
        if 'https' in host.services and 'backend_for' in host.props:
            backends = host.props['backend_for']
            if type(backends) == str:
                rv.append('%s,%s' % (host.name, backends))
            else:
                assert(type(backends) == list)
                for backend in backends:
                    rv.append('%s,%s' % (host.name, backend))
    return '\n'.join(rv)

@add_cmd('https_req', True, 2)
def gen_https_req(state, template, hostname, cn):
    return jinja2.Template(template).render(
        state=state, host=state.find(hostname), cn=cn)

@add_cmd('https_ca', True, 1)
def gen_https_ca(state, template, root):
    return jinja2.Template(template).render(state=state, root=root)
