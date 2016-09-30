from django.db import connection
from django.utils import six
from django_performance_testing.signals import before_clearing_queries_log
from django_performance_testing.core import \
    BaseLimit, BaseCollector, NameValueResult
from django_performance_testing.utils import DelegatingProxy


def setup_sending_before_clearing_queries_log_signal():
    class SignalSendingBeforeClearingQueriesProxy(DelegatingProxy):
        def clear(self):
            before_clearing_queries_log.send(sender=None, queries=tuple(self))
            self.wrapped.clear()

    connection.queries_log = SignalSendingBeforeClearingQueriesProxy(
        connection.queries_log)


class QueryCountResult(NameValueResult):

    def __init__(self, queries, name):
        self.queries = queries
        super(QueryCountResult, self).__init__(
            name=name, value=self.number_of_queries)

    @property
    def number_of_queries(self):
        return len(self.queries)


class QueryCollector(BaseCollector):

    type_name = 'queries'

    def __enter__(self):
        self.queries = []
        self.nr_of_queries_when_entering = len(connection.queries)
        self.orig_force_debug_cursor = connection.force_debug_cursor
        connection.force_debug_cursor = True
        before_clearing_queries_log.connect(
            self.queries_about_to_be_reset_handler)
        return self

    def queries_about_to_be_reset_handler(self,
                                          signal, sender, queries, **kwargs):
        self.store_queries()
        self.nr_of_queries_when_entering = 0

    def before_exit(self):
        before_clearing_queries_log.disconnect(
            self.queries_about_to_be_reset_handler)
        connection.force_debug_cursor = self.orig_force_debug_cursor
        self.store_queries()

    def get_results_to_send(self):
        by_type = dict(read=[], write=[], other=[])
        for result in self.queries:
            tp = classify_query(result['sql'])
            by_type[tp].append(result)
        by_type['total'] = self.queries
        return list(
            QueryCountResult(name=tp, queries=q)
            for (tp, q) in six.iteritems(by_type))

    def store_queries(self):
        self.queries += connection.queries[self.nr_of_queries_when_entering:]

_query_token_to_classification = {
    'SELECT': 'read',
    'INSERT': 'write',
    'UPDATE': 'write',
    'DELETE': 'write',
}


def classify_query(sql):
    if sql.startswith('QUERY ='):  # django 1.8
        without_query_prefix = sql.split(' = ')[1]
    else:
        without_query_prefix = sql

    first_token = without_query_prefix.split(' ')[0]
    pattern = '\''
    if pattern in first_token:
        query_type_token = first_token.split(pattern)[1]
    else:
        query_type_token = first_token
    return _query_token_to_classification.get(query_type_token, 'other')


class QueryBatchLimit(BaseLimit):
    collector_cls = QueryCollector

    quantifier = 'many'
    items_name = 'queries'
