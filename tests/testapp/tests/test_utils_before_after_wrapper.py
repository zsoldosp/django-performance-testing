from django_performance_testing.utils import BeforeAfterWrapper
import pytest


class TrackBeforeAfterCallCount(object):
    def __init__(self):
        self.before_call_count = 0
        self.after_call_count = 0

    def __enter__(self):
        self.before_call_count += 1
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.after_call_count += 1


def test_fails_when_class_has_no_such_method_as_to_wrap():
    with pytest.raises(AttributeError):
        BeforeAfterWrapper(
            wrapped_self=object(), method_to_wrap_name='no_such_method',
            context_manager=None)


def test_before_after_hooks_are_as_expected():
    class Foo(object):

        def foo(self):
            assert ctx.before_call_count == 1
            assert ctx.after_call_count == 0

    foo = Foo()
    ctx = TrackBeforeAfterCallCount()
    BeforeAfterWrapper(
        wrapped_self=foo, method_to_wrap_name='foo', context_manager=ctx)
    assert ctx.before_call_count == 0
    assert ctx.after_call_count == 0
    foo.foo()
    assert ctx.before_call_count == 1
    assert ctx.after_call_count == 1


def test_hooks_are_run_even_if_there_was_an_exception():
    class Bar(object):

        def will_fail(self):
            assert ctx.before_call_count == 1
            raise Exception('heh')

    bar = Bar()
    ctx = TrackBeforeAfterCallCount()
    BeforeAfterWrapper(
        wrapped_self=bar, method_to_wrap_name='will_fail', context_manager=ctx)
    with pytest.raises(Exception) as excinfo:
        bar.will_fail()
    assert str(excinfo.value) == 'heh'
    assert ctx.before_call_count == 1
    assert ctx.after_call_count == 1
