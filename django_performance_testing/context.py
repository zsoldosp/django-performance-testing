class Context(object):
    def __init__(self):
        self.data = {}

    def enter(self, key, value):
        self.data.setdefault(key, [])
        self.data[key].append(value)

    def exit(self, key, value):
        if key not in self.data:
            raise ValueError(
                'cannot exit not entered context - key {!r} mismatch'.format(
                    key
                )
            )
        values = self.data[key]
        enter_value = values[-1]
        if value != enter_value:
            raise ValueError(
                'cannot exit not entered context - value mismatch '
                '(exit: {!r}, enter: {!r})'.format(value, enter_value)
            )
        del values[-1]
        if not values:
            self.data.pop(key)

# current = Context()
