# TODO: app.ready happens before the command is imported - how to test?
from django.conf import settings
from django.test import utils
from django_performance_testing.reports import WorstReport
from django_performance_testing.utils import \
    multi_context_manager, wrap_cls_method_in_ctx_manager
from django_performance_testing.context import scoped_context
from django_performance_testing import core as djpt_core
import unittest

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


def wrap_cls_method(cls, method_name, collector_id, ctx_key, is_cls_method):
    ctx_value = '{} ({})'.format(
        method_name, unittest.util.strclass(cls))
    ctx = scoped_context(key=ctx_key, value=ctx_value)
    mcm = multi_context_manager(
        [ctx] + list((DjptTestRunnerMixin.collectors[collector_id]))
    )
    wrap_cls_method_in_ctx_manager(
        cls=cls, method_name=method_name, ctx_manager=mcm,
        is_cls_method=is_cls_method)


def get_runner_with_djpt_mixin(*a, **kw):
    test_runner_cls = orig_get_runner(*a, **kw)

    class DjptTestRunner(DjptTestRunnerMixin, test_runner_cls.test_runner):
        pass

    class DjptDjangoTestRunner(DjptDjangoTestRunnerMixin, test_runner_cls):

        test_runner = DjptTestRunner

    def addTest(suite_self, test):
        retval = orig_suite_addTest(suite_self, test)
        test_cls = test.__class__
        is_test = hasattr(test, '_testMethodName')
        if is_test:
            wrap_cls_method(
                cls=test_cls,
                method_name=test._testMethodName,
                collector_id='test method',
                ctx_key='test name',
                is_cls_method=False,
            )
            wrap_cls_method(
                cls=test_cls,
                method_name='setUp',
                collector_id='test setUp',
                ctx_key='setUp method',
                is_cls_method=False,
            )
            wrap_cls_method(
                cls=test_cls,
                method_name='tearDown',
                collector_id='test tearDown',
                ctx_key='tearDown method',
                is_cls_method=False,
            )
            wrap_cls_method(
                cls=test_cls,
                method_name='setUpClass',
                collector_id='test setUpClass',
                ctx_key='setUpClass method',
                is_cls_method=True,
            )
            wrap_cls_method(
                cls=test_cls,
                method_name='tearDownClass',
                collector_id='test tearDownClass',
                ctx_key='tearDownClass method',
                is_cls_method=True,
            )
        return retval

    def fn_to_id(fn):
        return fn.__code__.co_filename

    if fn_to_id(addTest) != fn_to_id(DjptDjangoTestRunner.test_suite.addTest):
        orig_suite_addTest = DjptDjangoTestRunner.test_suite.addTest
        DjptDjangoTestRunner.test_suite.addTest = addTest
    return DjptDjangoTestRunner


def integrate_into_django_test_runner():
    utils.get_runner = get_runner_with_djpt_mixin
    DjptTestRunnerMixin.collectors = {}
    DjptTestRunnerMixin.limits = {}
    collector_ids = [
        'test method', 'test setUp', 'test tearDown',
        'test setUpClass', 'test tearDownClass',
    ]
    for collector_id in collector_ids:
        collectors = DjptTestRunnerMixin.collectors[collector_id] = []
        limits = DjptTestRunnerMixin.limits[collector_id] = []
        for limit_cls in djpt_core.limits_registry.name2cls.values():
            collector = limit_cls.collector_cls(id_=collector_id)
            collectors.append(collector)
            limit = limit_cls(collector_id=collector_id, settings_based=True)
            limits.append(limit)
