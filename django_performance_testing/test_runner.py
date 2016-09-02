# TODO: app.ready happens before the command is imported - how to test?
from django.test import utils
from django_performance_testing.reports import WorstReport
from django_performance_testing.utils import BeforeAfterWrapper
from django_performance_testing import context

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


class DjptTestMethodBeforeAfterWrapper(BeforeAfterWrapper):

    def before_hook(self):
        context.current.enter(key='test name', value=str(self.wrapped_self))

    def after_hook(self):
        context.current.exit(key='test name', value=str(self.wrapped_self))


class DjptTestSuiteMixin(object):

    def addTest(self, test):
        retval = super(DjptTestSuiteMixin, self).addTest(test)
        is_test = hasattr(test, '_testMethodName')
        if is_test:
            DjptTestMethodBeforeAfterWrapper(test, test._testMethodName)
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
