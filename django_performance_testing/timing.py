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


class TimeLimit(BaseLimit):
    collector_cls = TimeCollector

    quantifier = 'many'
    items_name = 'elapsed seconds'
