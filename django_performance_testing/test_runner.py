# TODO: app.ready happens before the command is imported - how to test?
from django.conf import settings
from django.test import utils
from django_performance_testing.reports import WorstReport
from django_performance_testing.utils import BeforeAfterWrapper
from django_performance_testing.context import scoped_context
from django_performance_testing import core as djpt_core

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
        if getattr(settings, 'DJPT_PRINT_WORST_REPORT', True):
            self.djpt_worst_report.render(self.stream)
        return retval


class __NeededToFindInstanceMethodType(object):

    def some_method(self):
        pass


instancemethod = type(__NeededToFindInstanceMethodType().some_method)


def wrap_instance_method(instance, method_name, ctx_key, ctx_value):
    target_method = getattr(instance, method_name)
    if isinstance(target_method, instancemethod):
        for collector in DjptTestRunnerMixin.collectors:
            BeforeAfterWrapper(
                instance, method_name, context_manager=collector)
        ctx = scoped_context(key=ctx_key, value=ctx_value)
        BeforeAfterWrapper(
            instance, method_name, context_manager=ctx)


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
            wrap_instance_method(
                instance=test,
                method_name=test._testMethodName,
                ctx_key='test name',
                ctx_value=str(test))
        return retval

    def fn_to_id(fn):
        return fn.__code__.co_filename

    if fn_to_id(addTest) != fn_to_id(DjptDjangoTestRunner.test_suite.addTest):
        orig_suite_addTest = DjptDjangoTestRunner.test_suite.addTest
        DjptDjangoTestRunner.test_suite.addTest = addTest
    return DjptDjangoTestRunner


def integrate_into_django_test_runner():
    utils.get_runner = get_runner_with_djpt_mixin
    collector_id = 'test method'
    DjptTestRunnerMixin.collectors = []
    DjptTestRunnerMixin.limits = []
    for limit_cls in djpt_core.limits_registry.name2cls.values():
        collector = limit_cls.collector_cls(id_=collector_id)
        DjptTestRunnerMixin.collectors.append(collector)
        limit = limit_cls(collector_id=collector_id, settings_based=True)
        DjptTestRunnerMixin.limits.append(limit)
