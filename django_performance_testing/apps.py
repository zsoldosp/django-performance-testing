import django
from django.apps import AppConfig


class DjangoPerformanceTestingAppConfig(AppConfig):

    name = 'django_performance_testing'

    def ready(self):
        if django.VERSION[:2] == (1, 9):
            import warnings
            msg = "You are using an unsupported Django version. DJPT support" \
                  " might be dropped in any following release. See " \
                  "https://www.djangoproject.com/download/#supported-versions"
            warnings.warn(msg)

        from django_performance_testing.registry import \
            SettingsOrDefaultBasedRegistry
        from django_performance_testing import core
        core.limits_registry = SettingsOrDefaultBasedRegistry()
        from .test_client import integrate_into_test_client
        integrate_into_test_client()
        from .test_runner import integrate_into_django_test_runner
        integrate_into_django_test_runner()
        from .queries import setup_sending_before_clearing_queries_log_signal
        setup_sending_before_clearing_queries_log_signal()
        from .templates import integrate_into_django_templates
        integrate_into_django_templates()
