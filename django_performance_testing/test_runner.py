# TODO: app.ready happens before the command is imported - how to test?
from django.test import utils
from django_performance_testing.reports import WorstReport
from django_performance_testing.utils import BeforeAfterWrapper
from django_performance_testing.context import scoped_context
from django_performance_testing.queries import QueryCollector, QueryBatchLimit
from django_performance_testing.timing import TimeCollector, TimeLimit

orig_get_runner = utils.get_runner


class DjptDjangoTestRunnerMixin(object):
    pass


class DjptTestRunnerMixin(object):

    def run(self, *a, **kw):
        """
            as self.stopTestRun is ran before the actual results were printed,
            need to override run() to print things after
        """
        self.djpt_worst_report = WorstReport()
        retval = super(DjptTestRunnerMixin, self).run(*a, **kw)
        self.djpt_worst_report.render(self.stream)
        return retval


class DjptWrappedTestSuiteAddTest(object):
    def __init__(self, orig_suite_add_test):
        self.orig_suite_add_test = orig_suite_add_test


class __NeededToFindInstanceMethodType(object):

    def some_method(self):
        pass


instancemethod = type(__NeededToFindInstanceMethodType().some_method)


def get_runner_with_djpt_mixin(*a, **kw):
    test_runner_cls = orig_get_runner(*a, **kw)

    class DjptTestRunner(DjptTestRunnerMixin, test_runner_cls.test_runner):
        pass

    class DjptDjangoTestRunner(DjptDjangoTestRunnerMixin, test_runner_cls):

        test_runner = DjptTestRunner

    def addTest(suite_self, test):
        retval = orig_suite_addTest(suite_self, test)
        is_test = hasattr(test, '_testMethodName')
        if is_test:
            test_method = getattr(test, test._testMethodName)
            if isinstance(test_method, instancemethod):  # not patched yet
                test_ctx = scoped_context(key='test name', value=str(test))
                test_method_qcc = \
                    DjptTestRunnerMixin.test_method_querycount_collector
                time_ctx = DjptTestRunnerMixin.test_method_time_collector
                BeforeAfterWrapper(
                    test, test._testMethodName, context_manager=test_method_qcc
                )
                BeforeAfterWrapper(
                    test, test._testMethodName, context_manager=time_ctx)
                BeforeAfterWrapper(
                    test, test._testMethodName, context_manager=test_ctx)
        return retval

    def fn_to_id(fn):
        return fn.__code__.co_filename

    if fn_to_id(addTest) != fn_to_id(DjptDjangoTestRunner.test_suite.addTest):
        orig_suite_addTest = DjptDjangoTestRunner.test_suite.addTest
        DjptDjangoTestRunner.test_suite.addTest = addTest
    return DjptDjangoTestRunner


def integrate_into_django_test_runner():
    utils.get_runner = get_runner_with_djpt_mixin
    test_method_qc_id = 'test method'
    DjptTestRunnerMixin.test_method_querycount_collector = QueryCollector(
        id_=test_method_qc_id)
    DjptTestRunnerMixin.test_method_querycount_limit = QueryBatchLimit(
        collector_id=test_method_qc_id, settings_based=True)

    DjptTestRunnerMixin.test_method_time_collector = TimeCollector(
        id_=test_method_qc_id)
    DjptTestRunnerMixin.test_method_time_limit = TimeLimit(
        collector_id=test_method_qc_id, settings_based=True)
