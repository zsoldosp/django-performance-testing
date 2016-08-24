from django.apps import AppConfig


class DjangoPerformanceTestingAppConfig(AppConfig):

    name = 'django_performance_testing'

    def ready(self):
        from .test_client import integrate_into_test_client
        integrate_into_test_client()
