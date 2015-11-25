class ValueFromGroup(object):
    def __init__(self, value, source, depth):
        self.value  = value
        self.source = source
        self.depth  = depth

def fromgroup(value):
    return type(value) == ValueFromGroup

PRIMITIVES = {str: True, float: True, int: True, unicode: True}
def primitive(value):
    return type(value) in PRIMITIVES

def get_type(value):
    return type(value.value) if type(value) == ValueFromGroup else type(value)

class ValidationError(Exception):
    def __init__(self, msg):
        Exception.__init__(self, msg)
