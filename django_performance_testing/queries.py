from django.db import connection


class QueryCollector(object):

    def __init__(self, count_limit=None):
        self.count_limit = count_limit

    def __enter__(self):
        self.queries = []
        self.nr_of_queries_when_entering = len(connection.queries)
        # TODO: need to assert it's back to normal
        connection.force_debug_cursor = True
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # TODO: nested decorators/ctx managers
        self.queries = connection.queries[self.nr_of_queries_when_entering:]
        if self.count_limit is not None:
            nr_of_queries = len(self.queries)
            if nr_of_queries > self.count_limit:
                error_msg = 'Too many ({}) queries (limit: {})'.format(
                    nr_of_queries, self.count_limit)
                raise ValueError(error_msg)
