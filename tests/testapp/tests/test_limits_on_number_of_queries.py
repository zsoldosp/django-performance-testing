import pytest
from django.contrib.auth.models import Group
from django.db import connection
from django_performance_testing.queries import QueryCollector, QueryBatchLimit
from django_performance_testing.core import BaseLimit
from django_performance_testing.signals import result_collected


class TestQueryCollector(object):

    def test_captures_queries(self, db):
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

    def test_resets_connection_debugcursor_into_expected_state(self, db):
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

    def test_ctx_managers_can_be_nested(self, db):
        captured = {}

        def capture_signals(signal, sender, result, extra_context):
            captured.setdefault(sender, [])
            captured[sender].append(result)

        result_collected.connect(capture_signals)
        try:
            with QueryCollector() as outer:
                list(Group.objects.all())
                list(Group.objects.all())
                with QueryCollector() as inner:
                    list(Group.objects.all())
            assert {outer: [3], inner: [1]} == captured
        finally:
            result_collected.disconnect(capture_signals)


class TestQueryBatchLimit(object):
    def test_it_is_a_properly_wired_up_base_limit(self):
        assert issubclass(QueryBatchLimit, BaseLimit)
        assert QueryBatchLimit.collector_cls == QueryCollector
        assert QueryBatchLimit.result_collected_handler == \
            BaseLimit.result_collected_handler

    def test_when_exactly_limit_no__error(self):
        limit = QueryBatchLimit(count_limit=1)
        limit.handle_result(result=1, extra_context=None)
        assert True  # no exception raised

    def test_when_below_limit_no__error(self):
        limit = QueryBatchLimit(count_limit=3)
        limit.handle_result(result=0, extra_context=None)
        assert True  # no exception raised

    def test_when_above_limit_it_fails_with_meaningful_error_message(self):
        limit = QueryBatchLimit(count_limit=2)
        with pytest.raises(ValueError) as excinfo:
            limit.handle_result(result=3, extra_context=None)
        assert 'Too many (3) queries (limit: 2)' == str(excinfo.value)

    def test_given_extra_context_it_is_included_in_error_message(self):
        limit = QueryBatchLimit(count_limit=3)
        with pytest.raises(ValueError) as excinfo:
            limit.handle_result(
                result=4, extra_context={'extra': 'context'})
        assert 'Too many (4) queries (limit: 3) {\'extra\': \'context\'}' == \
            str(excinfo.value)

    def test_integration_test_with_db(self, db):
        with pytest.raises(ValueError) as excinfo:
            with QueryBatchLimit(count_limit=2) as limit:
                limit.collector.extra_context = {'some': 'context'}
                list(Group.objects.all())
                Group.objects.update(name='bar')
                Group.objects.create(name='group')
        assert 'Too many (3) queries (limit: 2) {\'some\': \'context\'}' == \
            str(excinfo.value)
