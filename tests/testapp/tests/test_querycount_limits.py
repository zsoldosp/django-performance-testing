import pytest
from django.contrib.auth.models import Group
from django_performance_testing.queries import \
    QueryCollector, QueryBatchLimit, QueryCountResult
from django_performance_testing.core import LimitViolationError
from testapp.test_helpers import override_current_context


def test_it_has_the_correct_collector():
    assert QueryBatchLimit.collector_cls == QueryCollector


def test_it_has_the_correct_attributes_for_limitviolationerror():
    assert QueryBatchLimit.quantifier == 'many'
    assert QueryBatchLimit.items_name == 'queries'


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
    assert excinfo.value.name == 'total'


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
    assert excinfo.value.name == 'a'

    with pytest.raises(LimitViolationError) as excinfo:
        limit.handle_results(results=[
            QueryCountResult(name='a', queries=range(0)),
            QueryCountResult(name='c', queries=range(2)),
            QueryCountResult(name='b', queries=range(5)),
        ], context=None)
    assert excinfo.value.actual == 5
    assert excinfo.value.limit == 2
    assert excinfo.value.name == 'b'


def test_limit_exceeded_failure_message_includes_collector_name_if_exists(db):
    with pytest.raises(LimitViolationError) as excinfo:
        collector = QueryBatchLimit.collector_cls(id_='collector_id_included')
        with QueryBatchLimit(collector_id='collector_id_included', read=0):
            with collector:
                list(Group.objects.all())
    assert excinfo.value.name == 'read (for collector_id_included)'


def test_can_specify_typed_limits(db):
    with pytest.raises(LimitViolationError) as excinfo:
        with QueryBatchLimit(write=0, read=3):
            list(Group.objects.all())
            list(Group.objects.all())
            list(Group.objects.all())
            Group.objects.update(name='foo')

    with pytest.raises(LimitViolationError) as excinfo:
        with QueryBatchLimit(read=0):
            list(Group.objects.all())
    assert excinfo.value.context == {}
    assert excinfo.value.actual == 1
    assert excinfo.value.limit == 0
    assert excinfo.value.name == 'read'

    with pytest.raises(LimitViolationError) as excinfo:
        with QueryBatchLimit(write=1):
            Group.objects.update(name='baz')
            Group.objects.update(name='name')
    assert excinfo.value.context == {}
    assert excinfo.value.actual == 2
    assert excinfo.value.limit == 1
    assert excinfo.value.name == 'write'
