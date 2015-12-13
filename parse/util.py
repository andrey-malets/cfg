class ValueFromGroup(object):
    def __init__(self, value, source, depth):
        self.value  = value
        self.source = source
        self.depth  = depth

PRIMITIVES = {str: True, float: True, int: True, unicode: True}
def is_primitive(value):
    return type(value) in PRIMITIVES

def is_from_group(value):
    return type(value) == ValueFromGroup

def get_value(value):
    assert is_primitive(value) or is_from_group(value)
    return value.value if is_from_group(value) else value

def get_depth(value):
    return value.depth if is_from_group(value) else 0

def get_type(value):
    return type(value.value) if is_from_group(value) else type(value)

def matches(stype, dtype):
    if stype in [unicode, str] and dtype in [unicode, str]:
        return True
    return stype == dtype

class ValidationError(Exception):
    def __init__(self, msg):
        Exception.__init__(self, msg)
