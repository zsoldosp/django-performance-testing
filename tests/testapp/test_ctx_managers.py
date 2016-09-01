from django_performance_testing import context
from django_performance_testing.signals import result_collected


class capture_result_collected(object):

    def __enter__(self):
        self.calls = []
        result_collected.connect(self.result_collected_handler)
        return self

    def result_collected_handler(self, signal, sender, result, context):
        self.calls.append(dict(
            sender=sender, signal=signal, result=result,
            context=context))

    def __exit__(self, exc_type, exc_val, exc_tb):
        result_collected.disconnect(self.result_collected_handler)


class override_current_context(object):
    def __enter__(self):
        self.orig_current_context = context.current
        context.current = context.Context()
        return context.current

    def __exit__(self, exc_type, exc_val, exc_tb):
        context.current = self.orig_current_context
