import pytest
from django_performance_testing.core import LimitViolationError


def test_required_arguments_are_limit_actual_name_and_context():
    with pytest.raises(TypeError):
        LimitViolationError(
            limit=3, name='foo', context=None)  # missing actual
    with pytest.raises(TypeError):
        LimitViolationError(
            actual=3, name='foo', context=None)  # missing limit
    with pytest.raises(TypeError):
        LimitViolationError(
            actual=2, name='foo', limit=0)  # missing context
    with pytest.raises(TypeError):
        LimitViolationError(
            actual=2, limit=0, context={})  # missing name
    lve = LimitViolationError(
        limit=1, actual=2, name='foo', context={'foo': 'bar'})
    assert lve is not None
    assert lve.limit == 1
    assert lve.actual == 2
    assert lve.context == {'foo': 'bar'}
    assert lve.name == 'foo'


@pytest.mark.parametrize(
    'name,limit,actual', [
        ('read', 3, 1), ('write', 1, 3), ('other', 12, 9999)
    ]
)
def test_has_translates_to_error_message_without_context(name, limit, actual):
    lve = LimitViolationError(
        name=name, limit=limit, actual=actual, context=None)
    assert str(lve) == 'Too many ({}) {} queries (limit: {})'.format(
        actual, name, limit)


@pytest.mark.parametrize(
    'context,expected_repr', [
        ({'a': 1, 'b': 2, 'c': 3}, " {'a': 1, 'b': 2, 'c': 3}"),
        ({'foo': 'bar', 'bar': 'baz'}, " {'bar': 'baz', 'foo': 'bar'}"),
        ({}, '')
    ]
)
def test_given_context_it_is_included_in_error_message(context, expected_repr):
    lve = LimitViolationError(name='total', limit=3, actual=5, context=context)
    assert str(lve) == \
        'Too many (5) total queries (limit: 3){}'.format(expected_repr)
