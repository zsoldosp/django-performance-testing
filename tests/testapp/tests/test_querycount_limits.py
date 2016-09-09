import pytest
from django.contrib.auth.models import Group
from django_performance_testing.queries import \
    QueryCollector, QueryBatchLimit, QueryCountResult
from django_performance_testing.core import BaseLimit
from testapp.test_helpers import override_current_context


def qcr(n):
    return QueryCountResult(name='total', queries=range(n))


def test_it_is_a_properly_wired_up_base_limit():
    assert issubclass(QueryBatchLimit, BaseLimit)
    assert QueryBatchLimit.collector_cls == QueryCollector
    assert QueryBatchLimit.results_collected_handler == \
        BaseLimit.results_collected_handler


def test_when_exactly_limit_no__error():
    limit = QueryBatchLimit(total=1)
    limit.handle_results(results=[qcr(1)], context=None)
    assert True  # no exception raised


def test_when_below_limit_no__error():
    limit = QueryBatchLimit(total=3)
    limit.handle_results(results=[qcr(0)], context=None)
    assert True  # no exception raised


def test_when_above_limit_it_fails_with_meaningful_error_message():
    limit = QueryBatchLimit(total=2)
    with pytest.raises(ValueError) as excinfo:
        limit.handle_results(results=[qcr(3)], context=None)
    assert 'Too many (3) queries (limit: 2)' == str(excinfo.value)


def test_given_context_it_is_included_in_error_message():
    limit = QueryBatchLimit(total=3)
    with pytest.raises(ValueError) as excinfo:
        limit.handle_results(
            results=[qcr(4)], context={'extra': 'context'})
    assert 'Too many (4) queries (limit: 3) {\'extra\': \'context\'}' == \
        str(excinfo.value)


def test_integration_test_with_db(db):
    with pytest.raises(ValueError) as excinfo:
        with override_current_context() as ctx:
            with QueryBatchLimit(total=2):
                ctx.enter(key='some', value='context')
                list(Group.objects.all())
                Group.objects.update(name='bar')
                Group.objects.create(name='group')
    assert 'Too many (3) queries (limit: 2) {\'some\': [\'context\']}' in \
        str(excinfo.value)


def test_can_specify_typed_limits(db):
    with QueryBatchLimit(write=0):
        list(Group.objects.all())
        list(Group.objects.all())
        list(Group.objects.all())
    with QueryBatchLimit(read=0):
        Group.objects.update(name='foo')
        Group.objects.create(name='bar')
    with pytest.raises(ValueError) as excinfo:
        with QueryBatchLimit(read=0):
            list(Group.objects.all())
    assert str(excinfo.value).endswith('Too many (1) queries (limit: 0)')
    with pytest.raises(ValueError) as excinfo:
        with QueryBatchLimit(write=1):
            Group.objects.update(name='baz')
            Group.objects.update(name='name')
    assert str(excinfo.value).endswith('Too many (2) queries (limit: 1)')
