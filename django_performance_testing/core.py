from django.conf import settings
from django_performance_testing.signals import results_collected


class LimitViolationError(RuntimeError):
    pass


class BaseLimit(object):

    def __init__(self, collector_id=None, settings_based=False, **data):
        self.settings_based = settings_based
        self._data = data
        self.collector_id = collector_id
        self._validate_data()
        if self.is_anonymous():
            self.collector = self.collector_cls()
        else:
            if self.collector_id not in self.collector_cls._ids:
                raise TypeError(
                    'There is no collector named {!r}'.format(collector_id))
            self.connect_for_results()
            self.collector = None

    def _validate_data(self):
        if not self.settings_based:
            return
        if self._data:
            raise TypeError(
                'Either provide data (kwargs) or settings_based, '
                'not both.')
        if self.is_anonymous():
            raise TypeError(
                'Can only be settings based when collector_id is provided.')

    @property
    def data(self):
        if not self.settings_based:
            return self._data
        app_settings = getattr(settings, 'PERFORMANCE_LIMITS', {})
        return app_settings.get(self.collector_id, {})

    def __enter__(self):
        if self.is_anonymous():
            self.connect_for_results()
            self.collector.__enter__()
        return self

    def connect_for_results(self):
        results_collected.connect(self.results_collected_handler)

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.is_anonymous():
            self.collector.__exit__(exc_type, exc_val, exc_tb)
            results_collected.disconnect(self.results_collected_handler)

    def is_anonymous(self):
        return self.collector_id is None

    def results_collected_handler(
            self, signal, sender, results, context, **kwargs):
        assert kwargs == {}, 'expected no kwargs, but got {!r}'.format(kwargs)
        if not self.is_anonymous():
            if self.collector_id != sender.id_:
                return
        else:
            if self.collector != sender:
                return
        self.handle_results(results=results, context=context)
