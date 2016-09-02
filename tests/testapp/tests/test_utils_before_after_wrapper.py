from django_performance_testing.utils import BeforeAfterWrapper
import pytest


class TrackHookCallCountBeforeAfterWrapper(BeforeAfterWrapper):
    def __init__(self, *a, **kw):
        super(TrackHookCallCountBeforeAfterWrapper, self).__init__(*a, **kw)
        self.before_call_count = 0
        self.after_call_count = 0

    def before_hook(self):
        self.before_call_count += 1

    def after_hook(self):
        self.after_call_count += 1


def test_fails_when_class_has_no_such_method_as_to_wrap():
    with pytest.raises(AttributeError):
        TrackHookCallCountBeforeAfterWrapper(
            wrapped_self=object(), method_to_wrap_name='no_such_method')


def test_before_after_hooks_are_as_expected():
    class Foo(object):

        def foo(self):
            assert wrapped.before_call_count == 1
            assert wrapped.after_call_count == 0

    foo = Foo()
    wrapped = TrackHookCallCountBeforeAfterWrapper(
        wrapped_self=foo, method_to_wrap_name='foo')
    assert wrapped.before_call_count == 0
    assert wrapped.after_call_count == 0
    foo.foo()
    assert wrapped.before_call_count == 1
    assert wrapped.after_call_count == 1


def test_hooks_are_run_even_if_there_was_an_exception():
    class Bar(object):

        def will_fail(self):
            raise Exception('heh')

    bar = Bar()
    wrapped = TrackHookCallCountBeforeAfterWrapper(
        wrapped_self=bar, method_to_wrap_name='will_fail')
    with pytest.raises(Exception) as excinfo:
        bar.will_fail()
    assert str(excinfo.value) == 'heh'
    assert wrapped.before_call_count == 1
    assert wrapped.after_call_count == 1
