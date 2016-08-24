import pprint
import pytest
from django.contrib.auth.models import Group
from django_performance_testing.queries import QueryCollector


def test_captures_queries(db):
    with QueryCollector() as qc_insert:
        Group.objects.create(name='foo')
    assert len(qc_insert.queries) == 1
    with QueryCollector() as qc_select:
        list(Group.objects.all())
    assert len(qc_select.queries) == 1
    with QueryCollector() as qc_update:
        Group.objects.update(name='bar')
    assert len(qc_update.queries) == 1
    with QueryCollector() as qc_delete:
        Group.objects.all().delete()
    delete_queries = list(
        x['sql'] for x in qc_delete.queries if 'DELETE' in x['sql'])
    assert len(delete_queries) != 0, qc_delete.queries


def test_can_specify_fail_limit_and_then_it_fails(db):
    with QueryCollector(count_limit=1) as qc_not_failing:
        list(Group.objects.all())
    assert len(qc_not_failing.queries) == qc_not_failing.count_limit
    with pytest.raises(ValueError) as excinfo:
        with QueryCollector(count_limit=0):
            list(Group.objects.all())
    assert 'Too many (1) queries (limit: 0)' == str(excinfo.value)
    with pytest.raises(ValueError) as excinfo:
        with QueryCollector(count_limit=2):
            list(Group.objects.all())
            list(Group.objects.all())
            list(Group.objects.all())
    assert 'Too many (3) queries (limit: 2)' == str(excinfo.value)


def test_can_specify_extra_context_for_error_message(db):
    extra_context = {'foo': 'bar', 'x': 'y'}
    qc = QueryCollector(count_limit=0, extra_context=extra_context)
    qc.queries = ['abc']
    expected_error_message = 'Too many (1) queries (limit: 0) {}'.format(
        pprint.pformat(extra_context))
    assert expected_error_message == qc.get_error_message()
    with pytest.raises(ValueError) as excinfo:
        with qc:
            list(Group.objects.all())
    assert expected_error_message == str(excinfo.value)


def test_resets_connection_debugcursor_into_expected_state(db):
    from django.db import connection
    assert connection.force_debug_cursor is False, \
        'before QC with non-debug connection'
    with QueryCollector():
        pass
    assert connection.force_debug_cursor is False, \
        'after QC with non-debug connection'

    try:
        connection.force_debug_cursor = True
        with QueryCollector():
            pass
        assert connection.force_debug_cursor is True, \
            'after QC with debug connection'
    finally:
        connection.force_debug_cursor = False
