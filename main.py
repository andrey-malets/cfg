#!/opt/local/bin/python2.7

import os, sys, yaml

from parse.state import State
from gen.cmd     import Cmd

if __name__ == '__main__':
    state = None
    router_attrs = {}
    for key, envname in {'dev': 'ROUTER_DEV', 'src': 'ROUTER_SRC'}.iteritems():
        router_attrs[key] = dict(map(lambda token: token.split(':'),
                                     os.environ.get(envname, '').split()))
    if 'CFG' in os.environ:
        with open(os.environ['CFG'], 'r') as cfgfile:
            state = State(yaml.load(cfgfile), router_attrs)
    else:
        state = State(yaml.load(sys.stdin), router_attrs)

    if len(state.errors):
        for error in state.errors: print >> sys.stderr, 'Error: %s' % error
        sys.exit(1)
    else:
        try:
            print Cmd.execute(state, sys.argv[1:])
        except Exception as e:
            print >> sys.stderr, e
            sys.exit(1)
