class ValueFromGroup(object):
    def __init__(self, value, source):
        self.value = value
        self.source = source

    def __str__(self):
        return self.value

def primitive(value):
    return type(value) in [str, float, int]

class ValidationError(Exception):
    def __init__(self, msg):
        self.msg = msg

    def __repr__(self):
        return self.msg

    def __str__(self):
        return self.msg
