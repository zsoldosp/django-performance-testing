from django.test.client import Client
from django_performance_testing import context
from django_performance_testing.queries import QueryCollector, QueryBatchLimit

orig_client_request = Client.request


def client_request_that_fails_for_too_many_queries(client_self, **request):
    key = 'Client.request'
    value = '{} {}'.format(request['REQUEST_METHOD'], request['PATH_INFO'])
    context.current.enter(key=key, value=value)
    try:
        with client_self._querycount_collector:
            return orig_client_request(client_self, **request)
    finally:
        context.current.exit(key=key, value=value)  # TODO: convert to ctx mgr


def integrate_into_test_client():
    id_ = 'django.test.client.Client'
    Client._querycount_collector = QueryCollector(id_=id_)
    Client._querycount_limit = QueryBatchLimit(
        collector_id=id_, settings_based=True)
    Client.request = client_request_that_fails_for_too_many_queries
