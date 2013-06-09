#!/opt/local/bin/python2.7

import sys, yaml

from parse.state import State
from gen.cmd     import Cmd

if __name__ == '__main__':
    state = State(yaml.load(sys.stdin))
    if len(state.errors):
        for error in state.errors: print >> sys.stderr, 'Error: %s' % error
        sys.exit(1)
    else:
        try:
            print Cmd.execute(state, sys.argv[1:])
        except Exception as e:
            print >> sys.stderr, e
            sys.exit(1)
