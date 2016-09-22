from django_performance_testing.utils import BeforeAfterWrapper


def test_wrapper_keeps_original_functions_attributes():

    class Foo(object):

        def foo(self):
            return 'bar'
        foo.returns = 'str'

    f = Foo()
    assert hasattr(f.foo, 'returns')  # before BeforeAfterWrapper
    assert 'str' == getattr(f.foo, 'returns')  # before BeforeAfterWrapper
    BeforeAfterWrapper(f, 'foo', context_manager=None)
    assert hasattr(f.foo, 'returns')  # after BeforeAfterWrapper
    assert 'str' == getattr(f.foo, 'returns')  # after BeforeAfterWrapper
