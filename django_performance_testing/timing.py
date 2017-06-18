from time import time
from django_performance_testing.core import \
    BaseCollector, BaseLimit, NameValueResult


class TimeCollector(BaseCollector):

    type_name = 'time'

    def __enter__(self):
        self.start = time()
        return self

    def get_results_to_send(self):
        return [NameValueResult(name='total', value=time() - self.start)]

    @classmethod
    def get_sample_results(cls):
        return [0.01, 1.00, 3.2]


class TimeLimit(BaseLimit):
    collector_cls = TimeCollector

    quantifier = 'many'
    items_name = 'elapsed seconds'
