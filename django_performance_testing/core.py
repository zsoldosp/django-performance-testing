from django_performance_testing.signals import result_collected


class BaseLimit(object):

    def __init__(self, collector_id=None):
        self.collector_id = collector_id
        if self.is_anonymous():
            self.collector = self.collector_cls()
        else:
            if self.collector_id not in self.collector_cls._ids:
                raise TypeError(
                    'There is no collector named {!r}'.format(collector_id))
            self.connect_for_results()
            self.collector = None

    def __enter__(self):
        if self.is_anonymous():
            self.connect_for_results()
            self.collector.__enter__()
        return self

    def connect_for_results(self):
        result_collected.connect(self.result_collected_handler)

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.is_anonymous():
            self.collector.__exit__(exc_type, exc_val, exc_tb)
            result_collected.disconnect(self.result_collected_handler)

    def is_anonymous(self):
        return self.collector_id is None

    def result_collected_handler(
            self, signal, sender, result, extra_context, **kwargs):
        assert kwargs == {}, 'expected no kwargs, but got {!r}'.format(kwargs)
        if not self.is_anonymous():
            if self.collector_id != sender.id_:
                return
        else:
            if self.collector != sender:
                return
        self.handle_result(result=result, extra_context=extra_context)
