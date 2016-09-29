from collections import namedtuple
from django.conf import settings
from django.test.utils import get_runner
from django.utils import six
from django_performance_testing import context
from django_performance_testing.signals import results_collected


WithId = namedtuple('WithId', ('id_',))


def run_testcase_with_django_runner(
        testcase_cls, nr_of_tests, all_should_pass=True, print_bad=True):
    django_runner_cls = get_runner(settings)
    django_runner = django_runner_cls()
    suite = django_runner.test_suite()
    tests = django_runner.test_loader.loadTestsFromTestCase(testcase_cls)
    suite.addTests(tests)
    test_runner = django_runner.test_runner(
        resultclass=django_runner.get_resultclass(),
        stream=six.StringIO()
    )
    result = test_runner.run(suite)
    assert result.testsRun == nr_of_tests
    unexpected = result.errors + result.failures
    if unexpected:
        if print_bad:
            for (test, msg) in unexpected:
                print('{}\n\n{}\n'.format(test, msg))
        assert not all_should_pass

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
        results_collected.connect(self.results_collected_handler)
        return self

    def results_collected_handler(self, signal, sender, results, context):
        self.calls.append(dict(
            sender=sender, signal=signal, results=results,
            context=context))

    def __exit__(self, exc_type, exc_val, exc_tb):
        results_collected.disconnect(self.results_collected_handler)


class override_current_context(object):
    def __enter__(self):
        self.orig_current_context = context.current
        context.current = context.Context()
        return context.current

    def __exit__(self, exc_type, exc_val, exc_tb):
        context.current = self.orig_current_context
