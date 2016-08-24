from django.apps import AppConfig
from django.test.client import Client
from django.utils import six
from django_performance_testing.queries import QueryCollector


class DjangoPerformanceTestingAppConfig(AppConfig):

    name = 'django_performance_testing'

    def ready(self):
        orig_client_request = Client.request

        def custom_client_request(client_self, **request):
            from django.conf import settings
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

        Client.request = custom_client_request
