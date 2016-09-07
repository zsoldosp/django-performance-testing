from django.apps import AppConfig


class DjangoPerformanceTestingAppConfig(AppConfig):

    name = 'django_performance_testing'

    def ready(self):
        from .test_client import integrate_into_test_client
        integrate_into_test_client()
        from .test_runner import integrate_into_django_test_runner
        integrate_into_django_test_runner()
        from .queries import setup_sending_before_clearing_queries_log_signal
        setup_sending_before_clearing_queries_log_signal()
        from .templates import integrate_into_django_templates
        integrate_into_django_templates()
