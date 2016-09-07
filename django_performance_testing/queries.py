import copy
import functools
import pprint
import traceback
from django.db import connection
from django.utils import six
from django_performance_testing.signals import \
    result_collected, before_clearing_queries_log
from django_performance_testing.core import BaseLimit
from django_performance_testing.utils import DelegatingProxy
from django_performance_testing import context


def setup_sending_before_clearing_queries_log_signal():
    class SignalSendingBeforeClearingQueriesProxy(DelegatingProxy):
        def clear(self):
            before_clearing_queries_log.send(sender=None, queries=tuple(self))
            self.wrapped.clear()

    connection.queries_log = SignalSendingBeforeClearingQueriesProxy(
        connection.queries_log)


@functools.total_ordering
class QueryCountResult(object):

    def __init__(self, queries):
        self.queries = queries

    @property
    def nr_of_queries(self):
        return len(self.queries)

    def _to_cmp_val(self, other):
        if type(other) in six.integer_types:
            return other
        if type(other) == QueryCountResult:
            return other.nr_of_queries
        raise NotImplementedError()

    def __lt__(self, other):
        return self.nr_of_queries < self._to_cmp_val(other)

    def __eq__(self, other):
        return self.nr_of_queries == self._to_cmp_val(other)

    def __str__(self):
        return str(self.nr_of_queries)


class QueryCollector(object):

    _ids = set()

    def __init__(self, id_=None):
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
        before_clearing_queries_log.connect(
            self.queries_about_to_be_reset_handler)
        return self

    def queries_about_to_be_reset_handler(self, signal, sender, queries):
        self.store_queries()
        self.nr_of_queries_when_entering = 0

    def __exit__(self, exc_type, exc_val, exc_tb):
        before_clearing_queries_log.disconnect(
            self.queries_about_to_be_reset_handler)
        connection.force_debug_cursor = self.orig_force_debug_cursor
        self.store_queries()
        signal_responses = result_collected.send_robust(
            sender=self, result=QueryCountResult(self.queries),
            context=copy.deepcopy(context.current.data))
        if exc_type is None:
            for (receiver, response) in signal_responses:
                if isinstance(response,  BaseException):
                    error_msg = '{}{}: {}'.format(
                        ''.join(traceback.format_tb(response.__traceback__)),
                        type(response).__name__,
                        str(response)
                    )
                    raise type(response)(error_msg)
                    raise response

    def store_queries(self):
        self.queries += connection.queries[self.nr_of_queries_when_entering:]

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
        return self.data.get('count_limit', None)

    def handle_result(self, result, context):
        if self.count_limit is None:
            return
        if result <= self.count_limit:
            return

        context_msg = ''
        if context:
            context_msg = ' {}'.format(
                pprint.pformat(context))
        error_msg = 'Too many ({}) queries (limit: {}){}'.format(
            result, self.count_limit, context_msg)
        raise ValueError(error_msg)
