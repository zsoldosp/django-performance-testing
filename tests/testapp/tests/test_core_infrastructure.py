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
