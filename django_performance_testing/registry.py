class UniqueNamedClassRegistry(object):
    def __init__(self, dotted_paths):
        self.name2cls = {}
