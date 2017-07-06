from django.conf import settings
from django.utils.six.moves import cPickle as pickle
from django_performance_testing.signals import results_collected, results_read

DEFAULT_DJPT_DATAFILE_PATH = 'djpt.results_collected'


def get_datafile_path():
    try:
        return settings.DJPT_DATAFILE_PATH
    except AttributeError:
        return DEFAULT_DJPT_DATAFILE_PATH


class Reader:
    def __init__(self, fpath):
        self.fpath = fpath

    def read_all(self):
        with open(self.fpath, 'rb') as f:
            data = f.read()
        if not data:
            return []
        deserialized = pickle.loads(data)
        for (sender, results, context) in deserialized:
            results_read.send(sender=sender, results=results, context=context)
        return deserialized


class Writer:
    def __init__(self, fpath):
        self.fpath = fpath

    def start(self):
        self.data = []
        results_collected.connect(self.handle_results_collected)

    def end(self):
        results_collected.disconnect(self.handle_results_collected)
        data = pickle.dumps(self.data, pickle.HIGHEST_PROTOCOL)
        # TODO: couldn't write a test to verify file is opened only here
        with open(self.fpath, 'wb') as f:
            f.write(data)

    def handle_results_collected(self, sender, results, context, **kwargs):
        self.handle_result(sender, results, context)

    def handle_result(self, sender, results, context):
        self.data.append((sender, results, context))
