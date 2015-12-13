from cmd import add_cmd
import json
from parse.state import Encoder

@add_cmd('show', False, 1)
def show(state, name):
    entity = state.find_entity(name)
    if entity:
        return json.dumps(entity.props, indent=2, cls=Encoder)
