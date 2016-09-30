import copy
from django.conf import settings
from django_performance_testing import context
from django_performance_testing.signals import results_collected
import functools
import pprint
import traceback


@functools.total_ordering
class NameValueResult(object):
    def __init__(self, name, value):
        self.name = name
        self.value = value

    def _to_cmp_val(self, other):
        if type(other) == type(self):
            return other.value
        try:
            # other is numeric
            # need it e.g.: to support _pytest.python.ApproxNonIterable
            x = bool(self.value == other)  # noqa: F841
            return other
        except TypeError:
            raise NotImplementedError()

    def __lt__(self, other):
        return self.value < self._to_cmp_val(other)

    def __eq__(self, other):
        return self.value == self._to_cmp_val(other)

    def __str__(self):
        return str(self.value)


class LimitViolationError(RuntimeError):

    def __init__(self, limit_obj, result, context, tb=None):
        self.limit_obj = limit_obj
        self.result = result
        self.context = context
        self.tb = tb
        super(LimitViolationError, self).__init__(self.error_msg)

    @property
    def error_msg(self):
        base = self.base_error_msg
        ctx = self.context_repr
        tb = self.tb_msg
        if ctx:
            ctx = ' {}'.format(ctx)
        if tb:
            tb = '\n{}'.format(tb)
        return ''.join([base, ctx, tb])

    @property
    def tb_msg(self):
        if self.tb:
            return self.tb
        return ''

    @property
    def context_repr(self):
        if self.context:
            return pprint.pformat(self.context)
        return ''

    @property
    def base_error_msg(self):
        return 'Too {} ({}) {} {}{} (limit: {})'.format(
            self.quantifier,
            self.actual,
            self.name,
            self.items_name,
            self.collector_text,
            self.limit
        )

    @property
    def quantifier(self):
        return self.limit_obj.quantifier

    @property
    def items_name(self):
        return self.limit_obj.items_name

    @property
    def name(self):
        return self.result.name

    @property
    def collector_text(self):
        if self.limit_obj.is_anonymous():
            return ''
        return ' (for {})'.format(self.limit_obj.collector_id)

    @property
    def actual(self):
        return str(self.result)

    @property
    def limit(self):
        return self.limit_obj.limit_for(self.result)

    def clone_with_more_info(self, orig_tb):
        return LimitViolationError(
            limit_obj=self.limit_obj, result=self.result,
            context=self.context, tb=orig_tb)


class BaseCollector(object):

    def __init__(self, id_=None):
        self.id_ = id_

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
        performance_limits = getattr(settings, 'PERFORMANCE_LIMITS', {})
        settings_for_id = performance_limits.get(self.collector_id, {})
        return settings_for_id.get(self.type_name, {})

    @property
    def type_name(self):
        return self.collector_cls.type_name

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
        if not isinstance(sender, self.collector_cls):
            return
        if not self.is_anonymous():
            if self.collector_id != sender.id_:
                return
        else:
            if self.collector != sender:
                return
        self.handle_results(results=results, context=context)

    def handle_results(self, results, context):
        for result in results:
            self.handle_result(result, context)

    def handle_result(self, result, context):
        limit = self.limit_for(result)
        if limit is None:
            return
        if result <= limit:
            return

        name = result.name
        if not self.is_anonymous():
            name += ' (for {})'.format(self.collector_id)
        raise LimitViolationError(
            limit_obj=self, result=result, context=context)

    def limit_for(self, result):
        return self.data.get(result.name)
