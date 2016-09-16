from django.contrib.auth.models import Group
from django.test.utils import get_runner
from django.utils import six
from django_performance_testing import test_runner as djpt_test_runner_module
from django_performance_testing.reports import WorstReport
from django_performance_testing.signals import results_collected
import pytest
from testapp.test_helpers import \
    WithId, run_testcase_with_django_runner, override_current_context
import unittest


def to_dotted_name(cls):
    return '.'.join([cls.__module__, cls.__name__])


class MyTestSuite(object):

    def addTest(self, test):
        pass


class MyTestRunner(object):
    pass


class MyDjangoTestRunner(object):
    test_runner = MyTestRunner
    test_suite = MyTestSuite


@pytest.mark.parametrize('runner_cls_name,test_runner_cls,test_suite_cls', [
    ('django.test.runner.DiscoverRunner',
        unittest.TextTestRunner, unittest.TestSuite),
    (to_dotted_name(MyDjangoTestRunner),
        MyTestRunner, MyTestSuite),
], ids=['vanilla runner', 'custom runner'])
def test_runner_keeps_default_classes_in_inheritance_chain(
        settings, runner_cls_name, test_runner_cls, test_suite_cls):
    settings.TEST_RUNNER = runner_cls_name
    django_runner_cls = get_runner(settings)

    def assert_is_djpt_mixin(cls, base_cls, mixin_base_name):
        fullname = 'django_performance_testing.test_runner.{}'.format(
            mixin_base_name)
        mixin_cls_name = '{}Mixin'.format(mixin_base_name)
        mixin_cls = getattr(djpt_test_runner_module, mixin_cls_name)
        assert fullname == to_dotted_name(cls)
        assert issubclass(cls, mixin_cls)
        assert cls.__mro__[1] == mixin_cls
        if any(isinstance(base_cls, str_tp) for str_tp in six.string_types):
            assert base_cls == to_dotted_name(cls.__mro__[2])
        elif isinstance(base_cls, type):
            assert issubclass(cls, base_cls)
            assert cls.__mro__[2] == base_cls
        else:
            raise NotImplementedError(
                'Cannot handle type {}'.format(type(base_cls)))

    assert_is_djpt_mixin(
        cls=django_runner_cls, base_cls=runner_cls_name,
        mixin_base_name='DjptDjangoTestRunner')
    assert_is_djpt_mixin(
        cls=django_runner_cls.test_runner, base_cls=test_runner_cls,
        mixin_base_name='DjptTestRunner')
    assert django_runner_cls.test_suite == test_suite_cls


def test_after_running_django_testcases_report_is_printed():

    class SampleTestCase(unittest.TestCase):

        def test_one(self):
            results_collected.send(
                sender=WithId('whatever'), results=[1],
                context={'test': 'one'})

        def test_two(self):
            results_collected.send(
                sender=WithId('whatever'), results=[2],
                context={'test': 'two'})
    test_run = run_testcase_with_django_runner(SampleTestCase, nr_of_tests=2)

    # actual test assertions
    test_runner = test_run['test_runner']
    assert isinstance(test_runner.djpt_worst_report, WorstReport)
    report_data = test_runner.djpt_worst_report.data
    assert 'whatever' in list(report_data.keys())
    whatever = report_data['whatever']['']
    assert whatever.value == 2
    assert whatever.context == {'test': 'two'}
    printed = test_run['out']
    assert printed.endswith(test_runner.djpt_worst_report.rendered())


def test_runner_sets_executing_test_method_as_context():

    class SomeTestCase(unittest.TestCase):
        def test_foo(self):
            assert 'test name' in ctx.data, ctx.data.keys()
            tests = ctx.data['test name']
            assert len(tests) == 1
            assert [str(self)] == tests

    with override_current_context() as ctx:
        run_testcase_with_django_runner(SomeTestCase, nr_of_tests=1)


def test_number_of_queries_per_test_method_can_be_limited(db, settings):

    class ATestCase(unittest.TestCase):
        def test_foo(self):
            assert len(Group.objects.all()) == 0

    settings.PERFORMANCE_LIMITS = {
        'test method': {'total': 0}
    }

    test_run = run_testcase_with_django_runner(
        ATestCase, nr_of_tests=1, all_should_pass=False)
    out = test_run['out']
    assert 'LimitViolationError: ' in out

    test_runner = test_run['test_runner']
    assert isinstance(test_runner.djpt_worst_report, WorstReport)
    report_data = test_runner.djpt_worst_report.data
    assert 'test method' in list(report_data.keys())
    worst_test_method = report_data['test method']['total']
    assert worst_test_method.value == 1
    assert len(worst_test_method.context) == 1
    worst_test = worst_test_method.context['test name']
    assert len(worst_test) == 1
    assert worst_test[0].startswith(
        'test_foo (testapp.tests.test_integrates_with_django_testrunner.')
    assert worst_test[0].endswith('.ATestCase)')
    assert out.endswith(test_runner.djpt_worst_report.rendered())
