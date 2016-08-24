from django.apps import AppConfig
from django.test.client import Client
from django_performance_testing.queries import QueryCollector


class DjangoPerformanceTestingAppConfig(AppConfig):

    name = 'django_performance_testing'

    def ready(self):
        orig_client_get = Client.get

        def custom_client_get(client_self, *a, **kw):
            from django.conf import settings
            app_settings = getattr(settings, 'PERFORMANCE_LIMITS', {})
            query_collector_kwargs = app_settings.get(
                'django.test.client.Client', {})
            with QueryCollector(**query_collector_kwargs):
                return orig_client_get(client_self, *a, **kw)

        Client.get = custom_client_get
