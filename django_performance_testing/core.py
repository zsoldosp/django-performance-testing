import copy
from django.conf import settings
from django_performance_testing import context
from django_performance_testing.signals import results_collected
import pprint
import traceback


class LimitViolationError(RuntimeError):

    def __init__(self, name, limit, actual, context, tb=None):
        self.name = name
        self.limit = limit
        self.actual = actual
        self.context = context

        context_msg = ''
        if context:
            context_msg = ' {}'.format(
                pprint.pformat(context))
        error_msg = 'Too many ({}) {} queries (limit: {}){}'.format(
            actual, name, limit, context_msg)  # TODO: add limit type here!
        if tb:
            error_msg += '\n{}'.format(tb)
        super(LimitViolationError, self).__init__(error_msg)

    def clone_with_more_info(self, orig_tb):
        return LimitViolationError(
            name=self.name, limit=self.limit, actual=self.actual,
            context=self.context, tb=orig_tb)


class BaseCollector(object):

    def __init__(self, id_=None):
        self.id_ = id_
        self.ensure_id_is_unique()

    def ensure_id_is_unique(self):
        if self.should_have_unique_id():
            if self.id_ in self._ids:
                id_ = self.id_
                self.id_ = None
                raise TypeError(
                        'There is already a collector named {!r}'.format(id_))
            self._ids.add(self.id_)

    def __del__(self):
        if self.should_have_unique_id():
            self._ids.remove(self.id_)

    def should_have_unique_id(self):
        return self.id_ is not None

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.before_exit()
        signal_responses = results_collected.send_robust(
            sender=self, results=self.get_results_to_send(),
            context=copy.deepcopy(context.current.data))
        if exc_type is None:
            for (receiver, response) in signal_responses:
                if isinstance(response,  BaseException):
                    orig_tb = ''.join(
                        traceback.format_tb(response.__traceback__))
                    error_msg = '{}{}: {}'.format(
                        orig_tb,
                        type(response).__name__,
                        str(response)
                    )
                    if hasattr(response, 'clone_with_more_info'):
                        new_exc = response.clone_with_more_info(
                            orig_tb=orig_tb)
                    else:
                        new_exc = type(response)(error_msg)
                    raise new_exc

    def get_results_to_send(self):
        raise NotImplementedError()

    def before_exit(self):
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
