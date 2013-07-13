class ValueFromGroup(object):
    def __init__(self, value, source):
        self.value = value
        self.source = source

def fromgroup(value):
    return type(value) == ValueFromGroup

def primitive(value):
    return type(value) in [str, float, int]

class ValidationError(Exception):
    def __init__(self, msg):
        Exception.__init__(self, msg)
