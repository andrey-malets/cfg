import config

from flask import abort, Flask, request, Response
from functools import wraps
from werkzeug.contrib.cache import SimpleCache
import handlers
import json
import os
import sys
import socket
import subprocess
import yaml

sys.path.append(os.path.join(os.path.dirname(__file__), os.pardir))
from parse.group import Group
from parse.state import Overrides, State
from parse.util import ValueFromGroup


class Encoder(json.JSONEncoder):

    def __init__(self, *args, **kwargs):
        super(Encoder, self).__init__(*args, **kwargs)

    def default(self, obj):
        if type(obj) is ValueFromGroup:
            return obj.value
        else:
            return super(Encoder, self).default(obj)


def quote_if_needed(value):
    return '"{}"'.format(value) if value[0] not in ['"', "'"] else value


application = Flask('override')
application.debug = True
cache = SimpleCache()


class authorized(object):
    def __init__(self, acl):
        self.hosts = dict((socket.gethostbyname(host), True) for host in acl)

    def __call__(self, f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            if request.remote_addr in self.hosts:
                return f(*args, **kwargs)
            else:
                abort(403)
        return wrapper


def load_state(state_fn, overrides_fn):
    with open(state_fn) as configfile:
        overrides = Overrides.load(overrides_fn)
        return State(yaml.load(configfile, Loader=yaml.CLoader),
                     overrides=overrides), overrides


def get_state(state_fn, overrides_fn):
    def md5(filename):
        return subprocess.check_output(
            ['md5sum', filename]).strip().split(' ', 1)[0]
    key = '{}{}'.format(md5(state_fn), md5(overrides_fn))
    rv = cache.get(key)
    if rv is None:
        rv = load_state(state_fn, overrides_fn)
        cache.set(key, rv)
    return rv


def with_entity(f):
    @wraps(f)
    def wrapper(name):
        state, overrides = get_state(config.CFG, config.DB)
        entity = state.find_entity(name)
        if entity is not None:
            return Response(f(state, overrides, entity), mimetype='text/plain')
        abort(404)
    return wrapper


def run_handlers():
    state, _ = get_state(config.CFG, config.DB)
    for handler in handlers.HANDLERS:
        handler(state)


run_handlers()


def format_to_json(result):
    return '{}\n'.format(json.dumps(result, cls=Encoder, indent=2))


@application.route('{}/<name>'.format(config.WEB_PATH), methods=["GET"])
@with_entity
def get(state, overrides, entity):
    if len(request.args) > 0:
        values = [format_to_json(entity.props.get(prop))
                  for prop in request.args]
        return ''.join(values)
    else:
        result = {'props': entity.props, 'name': entity.name}
        if type(entity) is Group:
            result['hosts'] = map(lambda host: host.name, entity.hosts)
        return format_to_json(result)


@application.route('{}/<name>'.format(config.WEB_PATH), methods=["POST"])
@authorized(config.ACL)
@with_entity
def post(state, overrides, entity):
    props = overrides.get(entity)
    for prop, value in request.form.iteritems():
        if value:
            props[prop] = json.loads(quote_if_needed(value))
        elif prop in props:
            del props[prop]
    overrides.save(config.DB)
    run_handlers()
    return ''


if __name__ == '__main__':
    application.run()
