from django.test.client import Client
from django_performance_testing.context import scoped_context
from django_performance_testing.queries import QueryCollector, QueryBatchLimit
from django_performance_testing.timing import TimeCollector, TimeLimit

orig_client_request = Client.request


def client_request_that_fails_for_too_many_queries(client_self, **request):
    key = 'Client.request'
    value = '{} {}'.format(request['REQUEST_METHOD'], request['PATH_INFO'])
    with scoped_context(key=key, value=value):
        with client_self._querycount_collector:
            with client_self._time_collector:
                return orig_client_request(client_self, **request)


def integrate_into_test_client():
    id_ = 'django.test.client.Client'
    Client._querycount_collector = QueryCollector(id_=id_)
    Client._querycount_limit = QueryBatchLimit(
        collector_id=id_, settings_based=True)
    Client._time_collector = TimeCollector(id_=id_)
    Client._time_limit = TimeLimit(collector_id=id_, settings_based=True)
    Client.request = client_request_that_fails_for_too_many_queries
