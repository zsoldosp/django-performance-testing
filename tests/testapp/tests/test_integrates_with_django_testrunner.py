from django.test.utils import get_runner
from django.conf import settings
from django_performance_testing.test_runner import \
    DjptDjangoTestRunnerMixin, DjptTestRunnerMixin
from django_performance_testing.reports import WorstReport
from django_performance_testing.signals import result_collected
import pytest
from testapp.test_helpers import WithId, run_django_testcase
import unittest


def to_dotted_name(cls):
    return '.'.join([cls.__module__, cls.__name__])


class MyTestRunner(object):
    pass


class MyDjangoTestRunner(object):
    test_runner = MyTestRunner


@pytest.mark.parametrize('runner_cls_name,test_runner_cls', [
    ('django.test.runner.DiscoverRunner', unittest.TextTestRunner),
    (to_dotted_name(MyDjangoTestRunner), MyTestRunner),
], ids=['vanilla runner', 'custom runner'])
def test_runner_keeps_default_classes_in_inheritance_chain(
        settings, runner_cls_name, test_runner_cls):
    settings.TEST_RUNNER = runner_cls_name
    django_runner_cls = get_runner(settings)

    assert 'django_performance_testing.test_runner.DjptDjangoTestRunner' == \
        to_dotted_name(django_runner_cls)
    assert issubclass(django_runner_cls, DjptDjangoTestRunnerMixin)
    assert django_runner_cls.__mro__[1] == DjptDjangoTestRunnerMixin
    assert runner_cls_name == to_dotted_name(django_runner_cls.__mro__[2])

    assert 'django_performance_testing.test_runner.DjptTestRunner' == \
        to_dotted_name(django_runner_cls.test_runner)
    assert issubclass(django_runner_cls.test_runner, test_runner_cls)
    assert issubclass(django_runner_cls.test_runner, DjptTestRunnerMixin)
    assert django_runner_cls.test_runner.__mro__[1] == DjptTestRunnerMixin
    assert django_runner_cls.test_runner.__mro__[2] == test_runner_cls


def test_after_running_django_testcases_report_is_printed():
    runner = get_runner(settings)

    class SampleTestCase(unittest.TestCase):

        def test_one(self):
            result_collected.send(
                sender=WithId('whatever'), result=1, context={'test': 'one'})

        def test_two(self):
            result_collected.send(
                sender=WithId('whatever'), result=2, context={'test': 'two'})
    test_run = run_django_testcase(
        testcase_cls=SampleTestCase, django_runner_cls=runner)
    # sanity check
    assert test_run['result'].testsRun == 2
    assert test_run['result'].errors == []
    assert test_run['result'].failures == []

    # actual test assertions
    test_runner = test_run['test_runner']
    assert isinstance(test_runner.djpt_worst_report, WorstReport)
    report_data = test_runner.djpt_worst_report.data
    assert list(report_data.keys()) == ['whatever']
    whatever = report_data['whatever']
    assert whatever.value == 2
    assert whatever.context == {'test': 'two'}
    printed = test_run['out']
    assert printed.endswith(test_runner.djpt_worst_report.rendered())
