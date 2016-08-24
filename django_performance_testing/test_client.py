from django.conf import settings
from django.test.client import Client
from django.utils import six
from django_performance_testing.queries import QueryCollector

orig_client_request = Client.request


def client_request_that_fails_for_too_many_queries(client_self, **request):
    app_settings = getattr(settings, 'PERFORMANCE_LIMITS', {})
    query_collector_kwargs = app_settings.get(
        'django.test.client.Client', {})
    assert 'extra_context' not in query_collector_kwargs
    path_info_as_text = six.text_type(request['PATH_INFO'])
    extra_context = {'Client.{}'.format(
        request['REQUEST_METHOD']): path_info_as_text}
    query_collector_kwargs['extra_context'] = extra_context
    with QueryCollector(**query_collector_kwargs):
        return orig_client_request(client_self, **request)


def integrate_into_test_client():
    Client.request = client_request_that_fails_for_too_many_queries
