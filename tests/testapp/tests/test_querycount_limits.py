import pytest
from django.contrib.auth.models import Group
from django_performance_testing.queries import \
    QueryCollector, QueryBatchLimit, QueryCountResult
from django_performance_testing.core import BaseLimit, LimitViolationError
from testapp.test_helpers import override_current_context


def wrapped_between_irrelevant_results(name, n):
    return [
        QueryCountResult(name='dont check before', queries=range(n + 1)),
        QueryCountResult(name=name, queries=range(n)),
        QueryCountResult(name='dont check after', queries=range(n + 2)),
    ]


def test_it_is_a_properly_wired_up_base_limit():
    assert issubclass(QueryBatchLimit, BaseLimit)
    assert QueryBatchLimit.collector_cls == QueryCollector
    assert QueryBatchLimit.results_collected_handler == \
        BaseLimit.results_collected_handler


@pytest.mark.parametrize('name,limit', [
    ('total', 1), ('total', 3),
    ('read', 3), ('read', 2),
    ('write', 6), ('write', 9),
])
def test_when_exactly_limit_no__error(name, limit):
    qlimit = QueryBatchLimit(**{name: limit})
    qlimit.handle_results(
        results=wrapped_between_irrelevant_results(name, limit), context=None)
    assert True  # no exception raised


@pytest.mark.parametrize('name,limit,queries', [
    ('total', 1, 0), ('total', 3, 2),
    ('read', 3, 2), ('read', 2, 1),
    ('write', 6, 4), ('write', 9, 7),
])
def test_when_below_limit_no__error(name, limit, queries):
    assert limit > queries, 'assumption'
    qlimit = QueryBatchLimit(**{name: limit})
    qlimit.handle_results(
        results=wrapped_between_irrelevant_results(name, queries),
        context=None)
    assert True  # no exception raised


above_limits_params = (
    'name,limit,queries', [
        ('total', 10, 11), ('total', 2, 4),
        ('read', 0, 2), ('read', 4, 7),
        ('write', 3, 6), ('write', 1, 2),
    ]
)


@pytest.mark.parametrize(*above_limits_params)
def test_when_above_limit_it_fails_with_correct_exc_args(name, limit, queries):
    assert limit < queries, 'assumption'
    qlimit = QueryBatchLimit(**{name: limit})
    with pytest.raises(LimitViolationError) as excinfo:
        qlimit.handle_results(
            results=wrapped_between_irrelevant_results(name, queries),
            context=None)
    assert excinfo.value.limit == limit
    assert excinfo.value.actual == queries
    assert not excinfo.value.context


def test_integration_test_with_db(db):
    with pytest.raises(LimitViolationError) as excinfo:
        with override_current_context() as ctx:
            with QueryBatchLimit(total=2):
                ctx.enter(key='some', value='context')
                list(Group.objects.all())
                Group.objects.update(name='bar')
                Group.objects.create(name='group')
    assert excinfo.value.context == {'some': ['context']}
    assert excinfo.value.actual == 3
    assert excinfo.value.limit == 2


def test_type_limit_checks_are_performed_in_alphabetic_order_of_type_name():
    limit = QueryBatchLimit(c=3, b=2, a=1)
    with pytest.raises(LimitViolationError) as excinfo:
        limit.handle_results(results=[
            QueryCountResult(name='b', queries=range(2)),
            QueryCountResult(name='a', queries=range(2)),
            QueryCountResult(name='c', queries=range(2)),
        ], context=None)
    assert excinfo.value.actual == 2
    assert excinfo.value.limit == 1

    with pytest.raises(LimitViolationError) as excinfo:
        limit.handle_results(results=[
            QueryCountResult(name='a', queries=range(0)),
            QueryCountResult(name='c', queries=range(2)),
            QueryCountResult(name='b', queries=range(5)),
        ], context=None)
    assert excinfo.value.actual == 5
    assert excinfo.value.limit == 2


def test_can_specify_typed_limits(db):
    with pytest.raises(LimitViolationError) as excinfo:
        with QueryBatchLimit(write=0, read=3):
            list(Group.objects.all())
            list(Group.objects.all())
            list(Group.objects.all())
            Group.objects.update(name='foo')

        Group.objects.create(name='bar')
    with pytest.raises(LimitViolationError) as excinfo:
        with QueryBatchLimit(read=0):
            list(Group.objects.all())
    assert excinfo.value.context == {}
    assert excinfo.value.actual == 1
    assert excinfo.value.limit == 0

    with pytest.raises(LimitViolationError) as excinfo:
        with QueryBatchLimit(write=1):
            Group.objects.update(name='baz')
            Group.objects.update(name='name')
    assert excinfo.value.context == {}
    assert excinfo.value.actual == 2
    assert excinfo.value.limit == 1
