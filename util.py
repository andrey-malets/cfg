class ValueFromGroup(object):
    def __init__(self, value, source):
        self.value = value
        self.source = source

    def __str__(self):
        return self.value

def primitive(value):
    return type(value) in [str, float, int]
