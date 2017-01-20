from django_performance_testing.utils import \
    BeforeAfterWrapper, wrap_cls_method_in_ctx_manager
import pytest


class ControllableContextManager(object):
    def __init__(self):
        self.before_call_count = 0
        self.after_call_count = 0

    def __enter__(self):
        self.before_call_count += 1
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.after_call_count += 1


def wrap_via_baw(wrapped_self, method_to_wrap_name, context_manager):
    BeforeAfterWrapper(
        wrapped_self=wrapped_self, method_to_wrap_name=method_to_wrap_name,
        context_manager=context_manager)


def wrap_via_cls_methods(wrapped_self, method_to_wrap_name, context_manager):
    wrap_cls_method_in_ctx_manager(
        cls=type(wrapped_self), method_name=method_to_wrap_name,
        ctx_manager=context_manager
    )


@pytest.fixture(params=[wrap_via_baw, wrap_via_cls_methods])
def wrapper(request):
    return request.param


def test_fails_when_class_has_no_such_method_as_to_wrap(wrapper):
    with pytest.raises(AttributeError):
        wrapper(
            wrapped_self=object(), method_to_wrap_name='no_such_method',
            context_manager=None)


def test_before_after_hooks_are_as_expected(wrapper):
    class Foo(object):

        def foo(self):
            assert ctx.before_call_count == 1
            assert ctx.after_call_count == 0

    foo = Foo()
    ctx = ControllableContextManager()
    wrapper(
        wrapped_self=foo, method_to_wrap_name='foo', context_manager=ctx)
    assert ctx.before_call_count == 0
    assert ctx.after_call_count == 0
    foo.foo()
    assert ctx.before_call_count == 1
    assert ctx.after_call_count == 1


def test_hooks_are_run_even_if_there_was_an_exception(wrapper):
    class Bar(object):

        def will_fail(self):
            assert ctx.before_call_count == 1
            raise Exception('heh')

    bar = Bar()
    ctx = ControllableContextManager()
    wrapper(
        wrapped_self=bar, method_to_wrap_name='will_fail', context_manager=ctx)
    with pytest.raises(Exception) as excinfo:
        bar.will_fail()
    assert str(excinfo.value) == 'heh'
    assert ctx.before_call_count == 1
    assert ctx.after_call_count == 1


def test_wrapper_keeps_original_functions_attributes(wrapper):

    class Foo(object):

        def foo(self):
            return 'bar'
        foo.returns = 'str'

    f = Foo()
    assert hasattr(f.foo, 'returns')  # before BeforeAfterWrapper
    assert 'str' == getattr(f.foo, 'returns')  # before BeforeAfterWrapper
    wrapper(f, 'foo', context_manager=None)
    assert hasattr(f.foo, 'returns')  # after BeforeAfterWrapper
    assert 'str' == getattr(f.foo, 'returns')  # after BeforeAfterWrapper
