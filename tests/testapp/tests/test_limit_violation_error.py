import pytest
from django_performance_testing.core import LimitViolationError


def test_required_arguments_are_limit_and_actual_and_context():
    with pytest.raises(TypeError):
        LimitViolationError(limit=3, context=None)  # missing actual
    with pytest.raises(TypeError):
        LimitViolationError(actual=3, context=None)  # missing limit
    with pytest.raises(TypeError):
        LimitViolationError(actual=2, limit=0)  # missing context
    lve = LimitViolationError(limit=1, actual=2, context={'foo': 'bar'})
    assert lve is not None
    assert lve.limit == 1
    assert lve.actual == 2
    assert lve.context == {'foo': 'bar'}


@pytest.mark.parametrize(
    'limit,actual', [
        (3, 1), (1, 3), (12, 9999)
    ]
)
def test_has_translates_to_error_message_without_context(limit, actual):
    lve = LimitViolationError(limit=limit, actual=actual, context=None)
    assert str(lve) == 'Too many ({}) queries (limit: {})'.format(
        actual, limit)


@pytest.mark.parametrize(
    'context,expected_repr', [
        ({'a': 1, 'b': 2, 'c': 3}, " {'a': 1, 'b': 2, 'c': 3}"),
        ({'foo': 'bar', 'bar': 'baz'}, " {'bar': 'baz', 'foo': 'bar'}"),
        ({}, '')
    ]
)
def test_given_context_it_is_included_in_error_message(context, expected_repr):
    lve = LimitViolationError(limit=3, actual=5, context=context)
    assert str(lve) == \
        'Too many (5) queries (limit: 3){}'.format(expected_repr)
