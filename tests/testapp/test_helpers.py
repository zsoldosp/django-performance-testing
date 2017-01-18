from collections import namedtuple
from django.conf import settings
from django.test.utils import get_runner
from django.utils import six
from django_performance_testing import context
from django_performance_testing.signals import results_collected


FakeSender = namedtuple('FakeSender', ('id_', 'type_name'))


class WithId(FakeSender):

    def __new__(cls, id_):
        return super(WithId, cls).__new__(cls, id_, 'type name')


class RunnerTestCasePackage(object):

    def __init__(self, testcases_to_run, nr_of_tests, all_should_pass=True,
                 print_bad=True, runner_options=None):
        runner_options = runner_options or {}
        self.nr_of_tests = nr_of_tests
        self.all_should_pass = all_should_pass
        self.print_bad = print_bad

        django_runner_cls = get_runner(settings)
        django_runner = django_runner_cls(**runner_options)
        self.suite = django_runner.test_suite()
        for testcase_cls in testcases_to_run:
            tests = django_runner.test_loader.loadTestsFromTestCase(
                testcase_cls)
            self.suite.addTests(tests)
        self.test_runner = django_runner.test_runner(
            resultclass=django_runner.get_resultclass(),
            stream=six.StringIO()
        )

    def run(self):
        result = self.test_runner.run(self.suite)
        unexpected = result.errors + result.failures
        if unexpected:
            if self.print_bad:
                for (test, msg) in unexpected:
                    print('{}\n\n{}\n'.format(test, msg))
            assert not self.all_should_pass
        else:
            assert self.all_should_pass
        assert result.testsRun == self.nr_of_tests
        return result


def run_testcases_with_django_runner(testcases_to_run, nr_of_tests,
                                     all_should_pass=True, print_bad=True,
                                     runner_options=None):
    if isinstance(testcases_to_run, type):
        testcases_to_run = [testcases_to_run]
    package = RunnerTestCasePackage(
        testcases_to_run, nr_of_tests, all_should_pass,
        print_bad, runner_options)
    result = package.run()
    return {
        "result": result,
        "output": result.stream.getvalue(),
        "runner": package.test_runner
    }


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
