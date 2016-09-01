try:
    from unittest.mock import patch
except:
    from mock import patch
import pytest
from django_performance_testing.signals import result_collected


class capture_result_collected(object):

    def __enter__(self):
        self.calls = []
        result_collected.connect(self.result_collected_handler)
        return self

    def result_collected_handler(self, signal, sender, result, extra_context):
        self.calls.append(dict(
            sender=sender, signal=signal, result=result,
            extra_context=extra_context))

    def __exit__(self, exc_type, exc_val, exc_tb):
        result_collected.disconnect(self.result_collected_handler)


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

    def test_signal_passes_along_extra_context(self, collector_cls):
        extra_context = {'extra': 'context'}
        with capture_result_collected() as captured:
            assert captured.calls == []
            with collector_cls(extra_context=extra_context) as collector:
                pass
        assert len(captured.calls) == 1
        params = captured.calls[0]
        assert params['sender'] == collector
        assert params['extra_context'] == extra_context


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

            def handle_result(self, result, extra_context):
                self.calls.append(
                    dict(result=result, extra_context=extra_context))

        return CallCapturingLimit(**kw)

    def test_listening_by_id_is_always_active(self, limit_cls):
        collector = limit_cls.collector_cls(id_='listen by id')
        limit = self.get_call_capturing_limit(
            limit_cls=limit_cls, collector_id='listen by id')
        result_collected.send(
            sender=collector, result=0,
            extra_context={'before': 'context manager'})
        with limit:
            result_collected.send(
                sender=collector, result=1,
                extra_context={'inside': 'context manager'})
        result_collected.send(
            sender=collector, result=2,
            extra_context={'after': 'context manager'})

        assert len(limit.calls) == 3
        assert limit.calls == [
            {'result': 0, 'extra_context': {'before': 'context manager'}},
            {'result': 1, 'extra_context': {'inside': 'context manager'}},
            {'result': 2, 'extra_context': {'after': 'context manager'}},
        ]

    def test_without_id_only_listens_while_a_context_manager(self, limit_cls):
        limit = self.get_call_capturing_limit(limit_cls=limit_cls)
        assert limit.collector_id is None
        result_collected.send(
            sender=limit.collector, result=0,
            extra_context={'before': 'context manager'})
        with limit:
            result_collected.send(
                sender=limit.collector, result=1,
                extra_context={'inside': 'context manager'})
            assert len(limit.calls) == 1
            assert limit.calls == [
                {'result': 1, 'extra_context': {'inside': 'context manager'}},
            ]
        limit.calls = []
        result_collected.send(
            sender=limit.collector, result=2,
            extra_context={'after': 'context manager'})
        assert len(limit.calls) == 0

    def test_only_listens_to_its_collector_named(self, limit_cls):
        listened_to = limit_cls.collector_cls(id_='has listener')
        unlistened = limit_cls.collector_cls(id_='no listeners')
        limit = self.get_call_capturing_limit(
            limit_cls=limit_cls, collector_id='has listener')
        result_collected.send(
            sender=listened_to, result=5, extra_context={'should': 'receive'})
        result_collected.send(
            sender=unlistened, result=6, extra_context={'not': 'received'})
        assert len(limit.calls) == 1
        assert limit.calls == [
            {'result': 5, 'extra_context': {'should': 'receive'}},
        ]

    def test_only_listens_to_its_collector_anonymous(self, limit_cls):
        limit = self.get_call_capturing_limit(limit_cls=limit_cls)
        listened_to = limit.collector
        unlistened = limit_cls.collector_cls(id_='no listeners')
        with limit:
            result_collected.send(
                sender=listened_to, result=99,
                extra_context={'should': 'receive'})
            result_collected.send(
                sender=unlistened, result=55,
                extra_context={'not': 'received'})
            assert len(limit.calls) == 1
            assert limit.calls == [
                {'result': 99, 'extra_context': {'should': 'receive'}},
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

# TODO: what to do w/ reports, where one'd listen on more than one collector?
