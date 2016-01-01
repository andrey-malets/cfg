import config

import fcntl
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
from parse.state import Encoder, Overrides, State


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


class locker(object):
    def __init__(self, fd, op):
        (self.fd, self.op) = (fd, op)

    def __enter__(self):
        fcntl.flock(self.fd, self.op)
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        fcntl.flock(self.fd, fcntl.LOCK_UN)


class locked(object):
    def __init__(self, lockfile, write=False):
        self.lockfile = lockfile
        self.write = write

    def __call__(self, f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            with open(self.lockfile, 'w' if self.write else 'r') as lockfile:
                with locker(lockfile, fcntl.LOCK_EX if self.write
                                      else fcntl.LOCK_SH) as lock:
                    return f(*args, **kwargs)

        return wrapper



def load_state(state_fn, overrides_fn):
    with open(state_fn) as configfile:
        overrides = Overrides.load(overrides_fn)
        return State(yaml.load(configfile, Loader=yaml.CLoader),
                     overrides=overrides), overrides


def get_state(state_fn, overrides_fn):
    if not os.path.exists(overrides_fn):
        return load_state(state_fn, overrides_fn)

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
@locked(config.LOCK)
@with_entity
def get(state, overrides, entity):
    if len(request.args) > 0:
        values = [format_to_json(entity.props.get(prop))
                  for prop in request.args]
        return ''.join(values)
    else:
        result = {'props': entity.props, 'name': entity.name}
        if type(entity) is Group:
            result['hosts'] = map(lambda (host, _): host.name, entity.hosts)
        else:
            result['sname'] = entity.sname
            result['groups'] = sorted(entity.groups)
        return format_to_json(result)


@application.route('{}/<name>'.format(config.WEB_PATH), methods=["POST"])
@authorized(config.ACL)
@locked(config.LOCK, write=True)
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
