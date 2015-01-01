class User:
    def __init__(self, data):
        assert(len(data) >= 3)
        self.nickname, self.name, self.email = data[0:3]
        self.props = data[3] if len(data) > 3 else {}
        self.CNs = self.props.get('CNs', [self.nickname])
