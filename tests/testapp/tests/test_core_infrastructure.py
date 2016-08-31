import pytest


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
