from time import time
from django_performance_testing.core import BaseCollector


class TimeCollector(BaseCollector):

    def __enter__(self):
        self.start = time()
        return self

    def get_results_to_send(self):
        return [time() - self.start]
