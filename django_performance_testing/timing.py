from time import time
from django_performance_testing.core import BaseCollector, BaseLimit


class TimeCollector(BaseCollector):

    def __enter__(self):
        self.start = time()
        return self

    def get_results_to_send(self):
        return [time() - self.start]


class TimeLimit(BaseLimit):
    collector_cls = TimeCollector

    settings_key = 'time'

    quantifier = 'many'
    items_name = 'elapsed seconds'
