import config

from flask import abort, Flask, request, Response
from functools import wraps
import handlers
import json
import os
import sys
import socket
import yaml

sys.path.append(os.path.join(os.path.dirname(__file__), os.pardir))
from parse.state import Overrides, State
from parse.host import Host


def quote_if_needed(value):
    return '"{}"'.format(value) if value[0] not in ['"', "'"] else value


application = Flask('override')
application.debug = True


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


def load_state(filename, overrides):
    with open(filename) as configfile:
        return State(yaml.load(configfile, Loader=yaml.CLoader),
                     overrides=overrides)


def with_entity(f):
    @wraps(f)
    def wrapper(name):
        overrides = Overrides.load(config.DB)
        state = load_state(config.CFG, overrides)
        entity = state.find_entity(name)
        if entity is not None:
            return Response(f(state, overrides, entity), mimetype='text/plain')
        abort(404)
    return wrapper


def run_handlers():
    state = load_state(config.CFG, Overrides.load(config.DB))
    for handler in handlers.HANDLERS:
        handler(state)


run_handlers()


@application.route('{}/<name>'.format(config.WEB_PATH), methods=["GET"])
@with_entity
def get(state, overrides, entity):
    if len(request.args) > 0:
        values = ['{}\n'.format(json.dumps(entity.props.get(prop), indent=2))
                  for prop in request.args]
        return ''.join(values)
    else:
        return '{}\n'.format(json.dumps(entity.props, indent=2))


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
