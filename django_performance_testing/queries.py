import pprint
from django.db import connection


class QueryCollector(object):

    def __init__(self, count_limit=None, extra_context=None):
        self.count_limit = count_limit
        self.extra_context = extra_context

    def __enter__(self):
        self.queries = []
        self.nr_of_queries_when_entering = len(connection.queries)
        self.orig_force_debug_cursor = connection.force_debug_cursor
        connection.force_debug_cursor = True
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        connection.force_debug_cursor = self.orig_force_debug_cursor
        self.queries = connection.queries[self.nr_of_queries_when_entering:]
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
