# TODO: app.ready happens before the command is imported - how to test?
from django.test import utils
from django_performance_testing.reports import WorstReport
from django_performance_testing.utils import BeforeAfterWrapper
from django_performance_testing.context import scoped_context

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


class DjptTestSuiteMixin(object):

    def addTest(self, test):
        retval = super(DjptTestSuiteMixin, self).addTest(test)
        is_test = hasattr(test, '_testMethodName')
        if is_test:
            test_ctx = scoped_context(key='test name', value=str(test))
            BeforeAfterWrapper(
                    test, test._testMethodName, context_manager=test_ctx)
        return retval


def get_runner_with_djpt_mixin(*a, **kw):
    test_runner_cls = orig_get_runner(*a, **kw)

    class DjptTestRunner(DjptTestRunnerMixin, test_runner_cls.test_runner):
        pass

    class DjptTestSuite(DjptTestSuiteMixin, test_runner_cls.test_suite):
        pass

    class DjptDjangoTestRunner(DjptDjangoTestRunnerMixin, test_runner_cls):

        test_runner = DjptTestRunner
        test_suite = DjptTestSuite

        def run_tests(self, *a, **kw):
            self.djpt_worst_report = WorstReport()
            return super(DjptDjangoTestRunner, self).run_tests(*a, **kw)

    return DjptDjangoTestRunner


def integrate_into_django_test_runner():
    utils.get_runner = get_runner_with_djpt_mixin
