import pprint
from django.db import connection
from django_performance_testing.signals import result_collected
from django_performance_testing.core import BaseLimit


class QueryCollector(object):

    _ids = set()

    def __init__(self, id_=None, extra_context=None):
        self.extra_context = extra_context
        self.id_ = id_
        self.ensure_id_is_unique()

    def ensure_id_is_unique(self):
        if self.should_have_unique_id():
            if self.id_ in self._ids:
                id_ = self.id_
                self.id_ = None
                raise TypeError(
                        'There is already a collector named {!r}'.format(id_))
            self._ids.add(self.id_)

    def __del__(self):
        if self.should_have_unique_id():
            self._ids.remove(self.id_)

    def should_have_unique_id(self):
        return self.id_ is not None

    def __enter__(self):
        self.queries = []
        self.nr_of_queries_when_entering = len(connection.queries)
        self.orig_force_debug_cursor = connection.force_debug_cursor
        connection.force_debug_cursor = True
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        connection.force_debug_cursor = self.orig_force_debug_cursor
        self.queries = connection.queries[self.nr_of_queries_when_entering:]
        result_collected.send(
            sender=self, result=len(self.queries),
            extra_context=self.extra_context)

_query_token_to_classification = {
    'SELECT': 'read',
    'INSERT': 'write',
    'UPDATE': 'write',
    'DELETE': 'write',
}


def classify_query(sql):
    without_query_prefix = sql.split(' = ')[1]
    without_repr_quotes = without_query_prefix.split('\'')[1]
    query_type_token = without_repr_quotes.split(' ')[0]
    return _query_token_to_classification[query_type_token]


class QueryBatchLimit(BaseLimit):
    collector_cls = QueryCollector

    @property
    def count_limit(self):
        return self.data['count_limit']

    def handle_result(self, result, extra_context):
        if result <= self.count_limit:
            return

        extra_context_msg = ''
        if extra_context:
            extra_context_msg = ' {}'.format(
                pprint.pformat(extra_context))
        error_msg = 'Too many ({}) queries (limit: {}){}'.format(
            result, self.count_limit, extra_context_msg)
        raise ValueError(error_msg)
