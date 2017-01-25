from django_performance_testing.utils import \
    wrap_cls_method_in_ctx_manager, multi_context_manager
import pytest


class ControllableContextManager(object):

    class TestException(Exception):
        pass

    events_in_order = []
    counter = 0

    @classmethod
    def reset_events(cls):
        cls.events_in_order = []
        cls.counter = 0

    def __init__(self, fail_in_method=None):
        self.counter = type(self).counter
        type(self).counter += 1
        self.before_call_count = 0
        self.after_call_count = 0
        self.fail_in_method = fail_in_method

    def __enter__(self):
        self.before_call_count += 1
        self.handle_method_was_called('__enter__')
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.after_call_count += 1
        self.handle_method_was_called('__exit__')

    def handle_method_was_called(self, current_method_name):
        self.events_in_order.append((self, current_method_name))
        if self.fail_in_method == current_method_name:
            raise self.TestException('as requested, failing')

    def __repr__(self):
        return str(self.counter)


def wrap_via_cls_methods(cls_to_wrap, method_to_wrap_name,
                         context_manager, is_cls_method):
    wrap_cls_method_in_ctx_manager(
        cls=cls_to_wrap, method_name=method_to_wrap_name,
        ctx_manager=context_manager, is_cls_method=is_cls_method
    )


@pytest.fixture(params=[wrap_via_cls_methods])
def wrapper(request):
    return request.param


def test_fails_when_class_has_no_such_method_as_to_wrap(wrapper):
    with pytest.raises(AttributeError):
        wrapper(
            cls_to_wrap=object, method_to_wrap_name='no_such_method',
            context_manager=None, is_cls_method=False)
    with pytest.raises(AttributeError):
        wrapper(
            cls_to_wrap=object, method_to_wrap_name='no_such_method',
            context_manager=None, is_cls_method=True)


def test_before_after_hooks_are_as_expected(wrapper):
    class Foo(object):

        def foo(self):
            assert ctx.before_call_count == 1
            assert ctx.after_call_count == 0

    foo = Foo()
    ctx = ControllableContextManager()
    wrapper(
        cls_to_wrap=Foo, method_to_wrap_name='foo', context_manager=ctx,
        is_cls_method=False)
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
        cls_to_wrap=Bar, method_to_wrap_name='will_fail', context_manager=ctx,
        is_cls_method=False)
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
    assert hasattr(f.foo, 'returns')  # before wrapping
    assert 'str' == getattr(f.foo, 'returns')  # before wrapping
    wrapper(f, 'foo', context_manager=None, is_cls_method=False)
    assert hasattr(f.foo, 'returns')  # after wrapping
    assert 'str' == getattr(f.foo, 'returns')  # after wrapping


def test_wrapper_can_be_applied_to_classmethods(wrapper):

    class Foo(object):
        has_been_called = False

        @classmethod
        def some_classmethod(cls, some_arg):
            assert cls == Foo
            assert some_arg == 'hello'
            cls.has_been_called = True

    ctx = ControllableContextManager()
    wrapper(Foo, 'some_classmethod', context_manager=ctx, is_cls_method=True)
    assert ctx.before_call_count == 0
    assert ctx.after_call_count == 0
    Foo.some_classmethod('hello')
    assert ctx.before_call_count == 1
    assert ctx.after_call_count == 1
    assert Foo.has_been_called


class TestMultiContextManager(object):

    def test_cant_construct_it_without_a_managers(self):
        with pytest.raises(ValueError):
            multi_context_manager([])

    def test_runs_a_single_context_manager(self):
        ControllableContextManager.reset_events()
        mgr = ControllableContextManager()
        with multi_context_manager([mgr]):
            pass

        expected_calls = [(mgr, '__enter__'), (mgr, '__exit__')]
        assert expected_calls == self.get_recorded_calls()

    def test_runs_all_context_managers(self):
        ControllableContextManager.reset_events()
        outer = ControllableContextManager()
        inner = ControllableContextManager()

        expected_calls = self.get_recorded_calls_for_nested_ctx_managers(
            outer, inner)
        assert expected_calls == [
            (outer, '__enter__'), (inner, '__enter__'),
            (inner, '__exit__'), (outer, '__exit__')
        ]

        ControllableContextManager.reset_events()
        with multi_context_manager([outer, inner]):
            pass

        assert expected_calls == self.get_recorded_calls()

    def test_when_inner_enter_fails(self):
        ControllableContextManager.reset_events()
        outer = ControllableContextManager()
        inner = ControllableContextManager(fail_in_method='__enter__')

        with pytest.raises(ControllableContextManager.TestException):
            self.run_nested_context_managers(outer, inner)
        expected_calls = self.get_recorded_calls()

        assert expected_calls == [
            (outer, '__enter__'), (inner, '__enter__'), (outer, '__exit__')
        ]

        ControllableContextManager.reset_events()
        with pytest.raises(ControllableContextManager.TestException):
            with multi_context_manager([outer, inner]):
                pass
        assert expected_calls == self.get_recorded_calls()

    def test_when_outer_enter_fails(self):
        ControllableContextManager.reset_events()
        outer = ControllableContextManager(fail_in_method='__enter__')
        inner = ControllableContextManager()

        with pytest.raises(ControllableContextManager.TestException):
            self.run_nested_context_managers(outer, inner)

        expected_calls = self.get_recorded_calls()
        assert expected_calls == [(outer, '__enter__')]

        ControllableContextManager.reset_events()
        with pytest.raises(ControllableContextManager.TestException):
            with multi_context_manager([outer, inner]):
                pass
        assert expected_calls == self.get_recorded_calls()

    def test_when_code_inside_context_managers_fails(self):
        ControllableContextManager.reset_events()
        outer = ControllableContextManager()
        inner = ControllableContextManager()

        def fail():
            raise NotImplementedError('hi')

        with pytest.raises(NotImplementedError):
            self.run_nested_context_managers(outer, inner, fn=fail)
        expected_calls = self.get_recorded_calls()
        assert expected_calls == [
            (outer, '__enter__'), (inner, '__enter__'),
            (inner, '__exit__'), (outer, '__exit__')
        ]

        ControllableContextManager.reset_events()
        with pytest.raises(NotImplementedError):
            with multi_context_manager([outer, inner]):
                fail()

        assert expected_calls == self.get_recorded_calls()

    def test_three_managers_middle_one_fails(self):
        """ this is like raising the LimitViolationError """
        ControllableContextManager.reset_events()
        outer = ControllableContextManager()
        middle = ControllableContextManager(fail_in_method='__exit__')
        inner = ControllableContextManager()

        ControllableContextManager.reset_events()
        with pytest.raises(ControllableContextManager.TestException):
            with outer:
                with middle:
                    with inner:
                        pass
        expected_calls = self.get_recorded_calls()
        assert expected_calls == [
            (outer, '__enter__'), (middle, '__enter__'), (inner, '__enter__'),
            (inner, '__exit__'), (middle, '__exit__'), (outer, '__exit__')
        ]
        ControllableContextManager.reset_events()
        with pytest.raises(ControllableContextManager.TestException):
            with multi_context_manager([outer, middle, inner]):
                pass
        assert expected_calls == self.get_recorded_calls()

    def get_recorded_calls_for_nested_ctx_managers(self,
                                                   outer, inner, fn=None):
        self.run_nested_context_managers(outer, inner, fn=fn)
        return self.get_recorded_calls()

    def run_nested_context_managers(self, outer, inner, fn=None):
        if fn is None:
            def noop(): return None
            fn = noop
        ControllableContextManager.reset_events()
        with outer:
            with inner:
                fn()
        return self.get_recorded_calls()

    def get_recorded_calls(self):
        return list(ControllableContextManager.events_in_order)
