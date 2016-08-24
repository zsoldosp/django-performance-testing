from django.db import connection


class QueryCollector(object):

    def __enter__(self):
        self.queries = []
        # TODO: need to assert it's back to normal
        connection.force_debug_cursor = True
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # TODO: needs to be a copy
        # TODO: nested decorators/ctx managers
        self.queries = connection.queries
