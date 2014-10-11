from parse.state import State
import sys, yaml

def config_test():
    with open('cfg/conf.yaml') as cfgfile:
        state = State(yaml.load(cfgfile), {'dev': {}, 'src': {}})
    assert len(state.errors) == 0, ', '.join(map(str, state.errors))
