import pytest
from django_performance_testing import serializer
from django_performance_testing.signals import results_collected
from testapp.test_helpers import FakeSender, WithId


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


def test_writer_writes_collected_results_fired_between_statt_stop(tmpfilepath):
    writer = serializer.Writer(tmpfilepath)
    results_collected.send(
        sender=WithId('before start'), results=[1],
        context={'before': 'start'})
    writer.start()
    results_collected.send(
        sender=WithId('after start'), results=[2],
        context={'after': 'start'})
    writer.end()
    results_collected.send(
        sender=WithId('after end'), results=[3],
        context={'after': 'end'})
    reader = serializer.Reader(tmpfilepath)
    deserialized = reader.read_all()
    assert deserialized == [(WithId('after start'), [2], {'after': 'start'})]


@pytest.mark.parametrize('sender_id,sender_type', [
        ('sender_id_1', 'sender_type_1'),
        ('sender_id_2', 'sender_type_2'),
    ])
def test_roundtrip_serialization_single_results(
        tmpfilepath, sender_id, sender_type, sample_result):
    sender = FakeSender(id_=sender_id, type_name=sender_type)
    context = {
        'setUp method': ['setUp (some.module.TestCase'],
    }
    writer = serializer.Writer(tmpfilepath)
    writer.start()
    writer.handle_result(sender=sender, results=sample_result, context=context)
    writer.end()
    reader = serializer.Reader(tmpfilepath)
    deserialized = reader.read_all()
    assert deserialized == [(sender, sample_result, context)]
