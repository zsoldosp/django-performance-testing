import pytest
from django.contrib.auth.models import Group
from django.core import signals
from django.db import connection, reset_queries
from django.db.transaction import atomic
from django_performance_testing.queries import QueryCollector
from django_performance_testing.signals import results_collected
from testapp.test_helpers import capture_result_collected


@pytest.mark.parametrize(
    'code,total_lo_limit,write_lo_limit,read_lo_limit',
    [
        (lambda: Group.objects.create(name='foo'), 1, 1, 0),
        (lambda: list(Group.objects.all()), 1, 0, 1),
        (lambda: Group.objects.update(name='bar'), 1, 1, 0),
        (lambda: Group.objects.all().delete(), 1, 1, 0),
    ], ids=['insert', 'select', 'update', 'delete'])
def test_captures_and_classifies_each_query_type(
        db, code, total_lo_limit, write_lo_limit, read_lo_limit):

    # 'coz of new, 'smart' delete need an item
    Group.objects.create(name='random')
    with capture_result_collected() as captured:
        with QueryCollector():
            code()
    assert len(captured.calls) == 1
    results = list(r for r in captured.calls[0]['results'])

    def result_by_name(tp):
        for r in results:
            if r.name == tp:
                return r
        return None

    def assert_lo_limit(name, lo_limit):
        actual = result_by_name(name)
        assert actual >= lo_limit, (name, actual.queries)

    assert_lo_limit('total', total_lo_limit)
    assert_lo_limit('write', write_lo_limit)
    assert_lo_limit('read', read_lo_limit)


def test_collects_other_sql_statements_too(db):
    with capture_result_collected() as captured:
        with QueryCollector():
            with atomic():
                Group.objects.create(name='sdf')

    assert len(captured.calls) == 1
    results = list(r for r in captured.calls[0]['results'])
    other_sql_results = list(r for r in results if r.name == 'other')
    assert len(other_sql_results) == 1
    other_sqls = other_sql_results[0]
    assert len(other_sqls.queries) == 2  # savepoint/release


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


def test_resets_connection_debugcursor_into_expected_state(db):
    assert connection.force_debug_cursor is False, \
        'before QC with non-debug connection'
    with QueryCollector():
        assert connection.force_debug_cursor is True, 'inside QC'
    assert connection.force_debug_cursor is False, \
        'after QC with non-debug connection'

    try:
        connection.force_debug_cursor = True
        with QueryCollector():
            assert connection.force_debug_cursor is True, 'inside QC'
        assert connection.force_debug_cursor is True, \
            'after QC with debug connection'
    finally:
        connection.force_debug_cursor = False


def test_ctx_managers_can_be_nested(db):
    captured = {}

    def capture_signals(signal, sender, results, context):
        captured.setdefault(sender, [])
        total, = (r for r in results if r.name == 'total')
        captured[sender].append(total)

    results_collected.connect(capture_signals)
    try:
        with QueryCollector() as outer:
            list(Group.objects.all())
            list(Group.objects.all())
            with QueryCollector() as inner:
                list(Group.objects.all())
        assert {outer: [3], inner: [1]} == captured
    finally:
        results_collected.disconnect(capture_signals)


def test_collector_can_live_through_request_reseting_queries(db):
    with QueryCollector() as qc:
        list(Group.objects.all())
        signals.request_started.send(sender=None)
        Group.objects.update(name='df')
        reset_queries()
        Group.objects.all().delete()

    assert len(qc.queries) == 3
