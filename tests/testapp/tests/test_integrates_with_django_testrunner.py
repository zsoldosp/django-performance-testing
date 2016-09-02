from django.test.utils import get_runner
from django.utils import six
from django_performance_testing import test_runner as djpt_test_runner_module
from django_performance_testing.reports import WorstReport
from django_performance_testing.signals import result_collected
import pytest
from testapp.test_helpers import \
    WithId, run_testcase_with_django_runner, override_current_context
import unittest


def to_dotted_name(cls):
    return '.'.join([cls.__module__, cls.__name__])


class MyTestSuite(object):
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
    assert_is_djpt_mixin(
        cls=django_runner_cls.test_suite, base_cls=test_suite_cls,
        mixin_base_name='DjptTestSuite')


def test_after_running_django_testcases_report_is_printed():

    class SampleTestCase(unittest.TestCase):

        def test_one(self):
            result_collected.send(
                sender=WithId('whatever'), result=1, context={'test': 'one'})

        def test_two(self):
            result_collected.send(
                sender=WithId('whatever'), result=2, context={'test': 'two'})
    test_run = run_testcase_with_django_runner(SampleTestCase, nr_of_tests=2)

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


def test_runner_sets_executing_test_method_as_context():

    class SomeTestCase(unittest.TestCase):
        def test_foo(self):
            assert 'test name' in ctx.data, ctx.data.keys()
            assert [str(self)] == ctx.data['test name']

    with override_current_context() as ctx:
        run_testcase_with_django_runner(SomeTestCase, nr_of_tests=1)
