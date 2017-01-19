from datetime import timedelta
from django.contrib.auth.models import Group
from django.test.utils import get_runner
from django.utils import six
from django_performance_testing import test_runner as djpt_test_runner_module
from freezegun import freeze_time
import pytest
from testapp.test_helpers import (override_current_context,
                                  run_testcases_with_django_runner)
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


def test_runner_sets_executing_test_method_as_context():

    class SomeTestCase(unittest.TestCase):
        def test_foo(self):
            assert 'test name' in ctx.data, ctx.data.keys()
            tests = ctx.data['test name']
            assert len(tests) == 1
            assert [str(self)] == tests

    with override_current_context() as ctx:
        run_testcases_with_django_runner(SomeTestCase, nr_of_tests=1)


class FailsDbLimit(object):
    limit_name = 'test method'
    limit_type = 'queries'
    limit_value = 0

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        return None

    def code_that_fails(self):
        assert len(Group.objects.all()) == 0


class FailsTimeLimit(object):
    limit_name = 'test method'
    limit_type = 'time'
    limit_value = 4

    def __enter__(self):
        self.freeze_ctx_mgr = freeze_time('2016-09-29 18:18:01')
        self.frozen_time = self.freeze_ctx_mgr.__enter__()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        return self.freeze_ctx_mgr.__exit__(exc_type, exc_val, exc_tb)

    def code_that_fails(self):
        self.frozen_time.tick(timedelta(seconds=5))


@pytest.mark.parametrize(
    'test_methods_added,method_name,limit_failer_cls', [
        (1, 'test_foo', FailsDbLimit),
        (1, 'test_foo', FailsTimeLimit),
    ])
def test_limits_can_be_set_on_testcase_methods(db, settings,
                                               test_methods_added, method_name,
                                               limit_failer_cls):
    failer = limit_failer_cls()
    settings.PERFORMANCE_LIMITS = {
        failer.limit_name: {
            failer.limit_type: {
                'total': failer.limit_value
            }
        }
    }

    with failer:
        class ATestCase(unittest.TestCase):

            def test_default(self):
                pass

        def do_stuff(self):
            failer.code_that_fails()

        setattr(ATestCase, method_name, do_stuff)
        test_run = run_testcases_with_django_runner(
            ATestCase, nr_of_tests=test_methods_added + 1,
            all_should_pass=False)
    assert 'LimitViolationError: ' in test_run["output"]
