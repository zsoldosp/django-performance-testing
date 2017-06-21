from django.utils.six.moves import cPickle as pickle
from django_performance_testing.signals import results_collected


class Reader:
    def __init__(self, fpath):
        self.fpath = fpath

    def read_all(self):
        with open(self.fpath, 'rb') as f:
            data = f.read()
        if not data:
            return []
        return pickle.loads(data)


class Writer:
    def __init__(self, fpath):
        self.fpath = fpath

    def start(self):
        self.f = open(self.fpath, 'wb')  # TODO: move it to end
        self.data = []
        results_collected.connect(self.handle_results_collected)

    def end(self):
        data = pickle.dumps(self.data, pickle.HIGHEST_PROTOCOL)
        self.f.write(data)
        self.f.close()

    def handle_results_collected(self, sender, results, context, **kwargs):
        self.handle_result(sender, results, context)

    def handle_result(self, sender, results, context):
        self.data.append((sender, results, context))
