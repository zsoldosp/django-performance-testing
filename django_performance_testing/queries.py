import pprint
from django.db import connection
from django_performance_testing.signals import result_collected


class QueryCollector(object):

    __ids = set()

    def __init__(self, id_=None, count_limit=None, extra_context=None):
        self.count_limit = count_limit
        self.extra_context = extra_context
        self.id_ = id_
        self.ensure_id_is_unique()

    def ensure_id_is_unique(self):
        if self.should_have_unique_id():
            if self.id_ in self.__ids:
                id_ = self.id_
                self.id_ = None
                raise TypeError(
                        'There is already a collector named {!r}'.format(id_))
            self.__ids.add(self.id_)

    def __del__(self):
        if self.should_have_unique_id():
            self.__ids.remove(self.id_)

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
        if self.count_limit is not None:
            if len(self.queries) > self.count_limit:
                raise ValueError(self.get_error_message())

    def get_error_message(self):
        extra_context_msg = ''
        if self.extra_context:
            extra_context_msg = ' {}'.format(
                pprint.pformat(self.extra_context))
        return 'Too many ({}) queries (limit: {}){}'.format(
            len(self.queries), self.count_limit, extra_context_msg)

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


class QueryBatchLimit(object):
    collector_cls = QueryCollector

    def __init__(self, collector_id=None):
        self.collector_id = collector_id
        if self.is_anonymous():
            self.collector = self.collector_cls()
        else:
            self.connect_for_results()
            self.collector = None

    def __enter__(self):
        if self.is_anonymous():
            self.connect_for_results()
        return self

    def connect_for_results(self):
        result_collected.connect(self.result_collected_handler)

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.is_anonymous():
            result_collected.disconnect(self.result_collected_handler)

    def is_anonymous(self):
        return self.collector_id is None

    def result_collected_handler(self, signal, sender, result, extra_context):
        if not self.is_anonymous():
            if self.collector_id != sender.id_:
                return
        else:
            if self.collector != sender:
                return
        self.handle_result(result=result, extra_context=extra_context)

    def handle_result(self, result, extra_context):
        pass
