import pytest


class First:

    @classmethod
    def get_sample_results(cls):
        return [['first', '1'], ['first', '2']]


class Second:

    @classmethod
    def get_sample_results(cls):
        return [['second', '1'], ['second', '2']]


@pytest.fixture(params=[First, Second])
def plugin_cls(request):
    return request.param


def pytest_generate_tests(metafunc):
    if 'plugin_cls_with_sample_result' in metafunc.fixturenames:
        plugin_cls_fixtures = metafunc._arg2fixturedefs['plugin_cls']
        assert len(plugin_cls_fixtures) == 1
        plugin_cls_fixture = plugin_cls_fixtures[0]
        sample_results = []
        ids = []
        for plugin_cls in plugin_cls_fixture.params:
            for i, sample in enumerate(plugin_cls.get_sample_results()):
                sample_results.append((plugin_cls, sample))
                ids.append('-sample{}-'.format(i))
        metafunc.parametrize(
            argnames='plugin_cls_with_sample_result',
            argvalues=sample_results,
            ids=ids
        )


@pytest.fixture
def sample_result(request, plugin_cls, plugin_cls_with_sample_result):
    if plugin_cls != plugin_cls_with_sample_result[0]:
        pytest.skip('this sample result is not for this plugin')
    result = plugin_cls_with_sample_result[-1]
    return result

def test_roundtrip_serialization(sample_result):
    assert False

