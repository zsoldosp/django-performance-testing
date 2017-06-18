import pytest
from django_performance_testing import serializer
from testapp.test_helpers import FakeSender


def pytest_generate_tests(metafunc):
    if 'collector_cls_with_sample_result' in metafunc.fixturenames:
        plugin_cls_fixtures = metafunc._arg2fixturedefs['collector_cls']
        assert len(plugin_cls_fixtures) == 1
        plugin_cls_fixture = plugin_cls_fixtures[0]
        sample_results = []
        ids = []
        for collector_cls in plugin_cls_fixture.params:
            for i, sample in enumerate(collector_cls.get_sample_results()):
                sample_results.append((collector_cls, sample))
                ids.append('-sample{}-'.format(i))
        metafunc.parametrize(
            argnames='collector_cls_with_sample_result',
            argvalues=sample_results,
            ids=ids
        )


@pytest.fixture
def sample_result(collector_cls, collector_cls_with_sample_result):
    if collector_cls != collector_cls_with_sample_result[0]:
        pytest.skip('this sample result is not for this plugin')
    result = collector_cls_with_sample_result[-1]
    return result


@pytest.mark.parametrize('sender_id,sender_type', [
        ('sender_id_1', 'sender_type_1'),
        ('sender_id_2', 'sender_type_2'),
    ])
def test_roundtrip_serialization(
        tmpfilepath, sender_id, sender_type, sample_result):
    sender = FakeSender(id_=sender_id, type_name=sender_type)
    writer = serializer.Writer(tmpfilepath)
    writer.start()
    writer.handle_result(sender=sender, result=sample_result)
    writer.end()
    reader = serializer.Reader(tmpfilepath)
    deserialized = reader.read_all()
    assert deserialized == [(sender, sample_result)]
