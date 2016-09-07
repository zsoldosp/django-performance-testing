import pytest
from django.contrib.auth.models import Group
from django_performance_testing.queries import QueryCollector, QueryBatchLimit
from django_performance_testing.core import BaseLimit
from testapp.test_helpers import override_current_context


class TestQueryBatchLimit(object):
    def test_it_is_a_properly_wired_up_base_limit(self):
        assert issubclass(QueryBatchLimit, BaseLimit)
        assert QueryBatchLimit.collector_cls == QueryCollector
        assert QueryBatchLimit.results_collected_handler == \
            BaseLimit.results_collected_handler

    def test_when_exactly_limit_no__error(self):
        limit = QueryBatchLimit(count_limit=1)
        limit.handle_results(results=[1], context=None)
        assert True  # no exception raised

    def test_when_below_limit_no__error(self):
        limit = QueryBatchLimit(count_limit=3)
        limit.handle_results(results=[0], context=None)
        assert True  # no exception raised

    def test_when_above_limit_it_fails_with_meaningful_error_message(self):
        limit = QueryBatchLimit(count_limit=2)
        with pytest.raises(ValueError) as excinfo:
            limit.handle_results(results=[3], context=None)
        assert 'Too many (3) queries (limit: 2)' == str(excinfo.value)

    def test_given_context_it_is_included_in_error_message(self):
        limit = QueryBatchLimit(count_limit=3)
        with pytest.raises(ValueError) as excinfo:
            limit.handle_results(
                results=[4], context={'extra': 'context'})
        assert 'Too many (4) queries (limit: 3) {\'extra\': \'context\'}' == \
            str(excinfo.value)

    def test_integration_test_with_db(self, db):
        with pytest.raises(ValueError) as excinfo:
            with override_current_context() as ctx:
                with QueryBatchLimit(count_limit=2):
                    ctx.enter(key='some', value='context')
                    list(Group.objects.all())
                    Group.objects.update(name='bar')
                    Group.objects.create(name='group')
        assert 'Too many (3) queries (limit: 2) {\'some\': [\'context\']}' in \
            str(excinfo.value)
