from collections import namedtuple
from django_performance_testing import context
from django_performance_testing.signals import result_collected
from django.utils import six


WithId = namedtuple('WithId', ('id_',))


def run_django_testcase(testcase_cls, django_runner_cls):
    django_runner = django_runner_cls()
    suite = django_runner.test_suite()
    tests = django_runner.test_loader.loadTestsFromTestCase(testcase_cls)
    suite.addTests(tests)
    test_runner = django_runner.test_runner(
        resultclass=django_runner.get_resultclass(),
        stream=six.StringIO()
    )
    result = test_runner.run(suite)
    return dict(
        django_runner=django_runner,
        suite=suite,
        test_runner=test_runner,
        result=result,
        out=result.stream.getvalue()
    )


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
