# TODO: app.ready happens before the command is imported - how to test?
from django.test import utils
from django_performance_testing.reports import WorstReport

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


def get_runner_with_djpt_mixin(*a, **kw):
    test_runner_cls = orig_get_runner(*a, **kw)

    class DjptTestRunner(DjptTestRunnerMixin, test_runner_cls.test_runner):
        pass

    class DjptDjangoTestRunner(DjptDjangoTestRunnerMixin, test_runner_cls):

        test_runner = DjptTestRunner

        def run_tests(self, *a, **kw):
            self.djpt_worst_report = WorstReport()
            return super(DjptDjangoTestRunner, self).run_tests(*a, **kw)

    return DjptDjangoTestRunner


def integrate_into_django_test_runner():
    utils.get_runner = get_runner_with_djpt_mixin
