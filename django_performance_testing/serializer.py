from django.utils.six.moves import cPickle as pickle


class Reader:
    def __init__(self, fpath):
        self.fpath = fpath

    def read_all(self):
        with open(self.fpath, 'rb') as f:
            data = f.read()
        return pickle.loads(data)


class Writer:
    def __init__(self, fpath):
        self.fpath = fpath

    def start(self):
        self.f = open(self.fpath, 'wb')
        self.data = []

    def end(self):
        data = pickle.dumps(self.data, pickle.HIGHEST_PROTOCOL)
        self.f.write(data)
        self.f.close()

    def handle_result(self, sender, result):
        self.data.append((sender, result))
