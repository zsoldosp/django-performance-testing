from time import time
from django_performance_testing.signals import results_collected
# from django_performance_testing import context


class TimeCollector(object):
    def __enter__(self):
        self.start = time()

    def __exit__(self, exc_type, exc_val, exc_tb):
        results_collected.send_robust(
            sender=self, results=time() - self.start,
            context=None)
