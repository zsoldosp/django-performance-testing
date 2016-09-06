try:
    from unittest.mock import patch, Mock
except:
    from mock import patch, Mock
import pytest
from django_performance_testing.signals import result_collected
from testapp.test_helpers import \
    override_current_context, capture_result_collected


class TestCollectors(object):

    def test_can_create_without_id(self, collector_cls):
        collector = collector_cls()
        assert collector.id_ is None

    def test_can_create_multiple_without_id(self, collector_cls):
        collector_one = collector_cls()
        assert collector_one.id_ is None
        collector_two = collector_cls()
        assert collector_two.id_ is None

    def test_cannot_create_multiple_with_same_id(self, collector_cls):
        # if not assigned, it would be deleted straight away
        collector_foo = collector_cls(id_='foo')  # noqa: F841
        with pytest.raises(TypeError) as excinfo:
            collector_cls(id_='foo')
        assert 'There is already a collector named \'foo\'' in \
            str(excinfo.value)

    def test_when_it_is_deleted_its_id_is_freed(self, collector_cls):
        collector_one = collector_cls(id_='bar')
        del collector_one
        collector_two = collector_cls(id_='bar')
        assert collector_two.id_ == 'bar'

    def test_sends_a_signal_when_context_is_exited(self, collector_cls):
        with capture_result_collected() as captured:
            assert captured.calls == []
            with collector_cls():
                pass
            assert len(captured.calls) == 1
            with collector_cls():
                pass
            assert len(captured.calls) == 2

    def test_signal_passes_along_current_contexts_copy(self, collector_cls):
        with override_current_context() as ctx:
            ctx.enter(key='extra', value='context')
            with capture_result_collected() as captured:
                assert captured.calls == []
                with collector_cls() as collector:
                    pass
        assert len(captured.calls) == 1
        params = captured.calls[0]
        assert params['sender'] == collector
        received_context = params['context']
        assert received_context == {'extra': ['context']}
        assert received_context == ctx.data
        assert id(received_context) != id(ctx.data)
        assert received_context['extra'] == ctx.data['extra']
        assert id(received_context['extra']) != id(ctx.data['extra'])


class TestLimits(object):
    def test_limit_knows_its_collector(self, limit_cls):
        assert hasattr(limit_cls, 'collector_cls')
        assert isinstance(limit_cls.collector_cls, type)

    def test_creating_with_id_doesnt_create_own_collector(self, limit_cls):
        collector = limit_cls.collector_cls(id_='bar')  # noqa: F841
        limit = limit_cls(collector_id='bar')
        assert limit.collector_id == 'bar'
        assert limit.collector is None

    def test_cannot_create_with_id_not_matching_a_collector(self, limit_cls):
        with pytest.raises(TypeError) as excinfo:
            limit_cls(collector_id='no such collector')
        assert 'There is no collector named \'no such collector\'' in \
            str(excinfo.value)

    def test_creating_without_id_creates_its_own_collector(self, limit_cls):
        limit = limit_cls()
        assert isinstance(limit.collector, limit_cls.collector_cls)
        assert limit.collector_id is None


class TestLimitsListeningOnSignals(object):

    def get_call_capturing_limit(self, limit_cls, **kw):

        class CallCapturingLimit(limit_cls):
            calls = []

            def handle_result(self, result, context):
                self.calls.append(
                    dict(result=result, context=context))

        return CallCapturingLimit(**kw)

    def test_listening_by_id_is_always_active(self, limit_cls):
        collector = limit_cls.collector_cls(id_='listen by id')
        limit = self.get_call_capturing_limit(
            limit_cls=limit_cls, collector_id='listen by id')
        result_collected.send(
            sender=collector, result=0,
            context={'before': 'context manager'})
        with limit:
            result_collected.send(
                sender=collector, result=1,
                context={'inside': 'context manager'})
        result_collected.send(
            sender=collector, result=2,
            context={'after': 'context manager'})

        assert len(limit.calls) == 3
        assert limit.calls == [
            {'result': 0, 'context': {'before': 'context manager'}},
            {'result': 1, 'context': {'inside': 'context manager'}},
            {'result': 2, 'context': {'after': 'context manager'}},
        ]

    def test_without_id_only_listens_while_a_context_manager(self, limit_cls):
        limit = self.get_call_capturing_limit(limit_cls=limit_cls)
        assert limit.collector_id is None
        result_collected.send(
            sender=limit.collector, result=0,
            context={'before': 'context manager'})
        with limit:
            result_collected.send(
                sender=limit.collector, result=1,
                context={'inside': 'context manager'})
            assert len(limit.calls) == 1
            assert limit.calls == [
                {'result': 1, 'context': {'inside': 'context manager'}},
            ]
        limit.calls = []
        result_collected.send(
            sender=limit.collector, result=2,
            context={'after': 'context manager'})
        assert len(limit.calls) == 0

    def test_only_listens_to_its_collector_named(self, limit_cls):
        listened_to = limit_cls.collector_cls(id_='has listener')
        unlistened = limit_cls.collector_cls(id_='no listeners')
        limit = self.get_call_capturing_limit(
            limit_cls=limit_cls, collector_id='has listener')
        result_collected.send(
            sender=listened_to, result=5, context={'should': 'receive'})
        result_collected.send(
            sender=unlistened, result=6, context={'not': 'received'})
        assert len(limit.calls) == 1
        assert limit.calls == [
            {'result': 5, 'context': {'should': 'receive'}},
        ]

    def test_only_listens_to_its_collector_anonymous(self, limit_cls):
        limit = self.get_call_capturing_limit(limit_cls=limit_cls)
        listened_to = limit.collector
        unlistened = limit_cls.collector_cls(id_='no listeners')
        with limit:
            result_collected.send(
                sender=listened_to, result=99,
                context={'should': 'receive'})
            result_collected.send(
                sender=unlistened, result=55,
                context={'not': 'received'})
            assert len(limit.calls) == 1
            assert limit.calls == [
                {'result': 99, 'context': {'should': 'receive'}},
            ]

    def test_anonymous_enter_exit_calls_same_on_its_collector(self, limit_cls):
        limit = limit_cls()
        with patch.object(limit.collector, '__enter__') as enter_mock:
            with patch.object(limit.collector, '__exit__') as exit_mock:
                enter_mock.assert_not_called()
                exit_mock.assert_not_called()
                with limit:
                    enter_mock.assert_called_once_with()
                exit_mock.assert_called_once_with(None, None, None)

    def test_anonymous_quits_from_signal_after_collector_exit(self, limit_cls):
        limit = self.get_call_capturing_limit(limit_cls=limit_cls)
        with limit:
            pass
        assert len(limit.calls) == 1

    def test_signals_to_all_listeners_reports_first_failure(self, limit_cls):
        limit = limit_cls()

        class MyException(Exception):
            pass

        first_attached_handler = Mock()
        last_attached_handler = Mock()
        result_collected.connect(first_attached_handler)
        with patch.object(limit, 'handle_result') as handle_result_mock:
            handle_result_mock.side_effect = MyException('foo')
            with pytest.raises(MyException) as excinfo:
                with limit:
                    result_collected.connect(last_attached_handler)
        assert handle_result_mock.called
        result_collected.disconnect(first_attached_handler)
        result_collected.disconnect(last_attached_handler)
        assert str(excinfo.value) == 'foo'
        assert first_attached_handler.called
        assert last_attached_handler.called

    def test_signal_handler_error_doesnt_hide_inner_ctx_error(self, limit_cls):
        limit = limit_cls()
        with patch.object(limit, 'handle_result') as handle_result_mock:
            handle_result_mock.side_effect = Exception('handler error')
            with pytest.raises(Exception) as excinfo:
                with limit:
                    raise Exception('actual code error')
        assert str(excinfo.value) == 'actual code error'
        assert handle_result_mock.called


class TestCreatingSettingsBasedLimits(object):

    def test_cannot_provide_both_data_and_settings_based_true(self, limit_cls):
        collector = limit_cls.collector_cls(id_='some id')  # noqa: F841
        with pytest.raises(TypeError) as excinfo:
            limit_cls(collector_id='some id', data={}, settings_based=True)
        assert 'Either provide data (kwargs) or settings_based, not both.' == \
            str(excinfo.value)

    def test_values_based_on_setting_runtime_value(self, limit_cls, settings):
        id_ = 'runtime settings based limit'
        collector = limit_cls.collector_cls(id_=id_)  # noqa: F841
        limit = limit_cls(collector_id=id_, settings_based=True)
        settings.PERFORMANCE_LIMITS = {}
        assert limit.data == {}
        settings.PERFORMANCE_LIMITS = {id_: {'data': 'foo'}}
        assert limit.data == {'data': 'foo'}
        settings.PERFORMANCE_LIMITS = {id_: {'whatever': 'bar'}}
        assert limit.data == {'whatever': 'bar'}

    def test_when_providing_kwargs_data_that_is_obtained(self, limit_cls):
        collector = limit_cls.collector_cls(id_='kwarg data')  # noqa: F841
        limit = limit_cls(collector_id='kwarg data', foo='bar')
        assert limit.data == {'foo': 'bar'}

    def test_without_collector_id_cannot_be_settings_based(self, limit_cls):
        with pytest.raises(TypeError) as excinfo:
            limit_cls(settings_based=True)
        assert 'Can only be settings based when collector_id is provided.' == \
            str(excinfo.value)

    def test_when_no_data_in_settings_dont_fail(self, limit_cls, settings):
        id_ = 'settings has no value for this limit'
        collector = limit_cls.collector_cls(id_=id_)  # noqa: F841
        limit = limit_cls(collector_id=id_, settings_based=True)
        settings.PERFORMANCE_LIMITS = {}
        assert limit.data == {}
        limit.handle_result(result=1, context={})  # no error is raised

# TODO: what to do w/ reports, where one'd listen on more than one collector?
