import pytest
from django_performance_testing.queries import QueryCollector, QueryBatchLimit
from django_performance_testing.timing import TimeCollector, TimeLimit


@pytest.fixture(params=[QueryCollector, TimeCollector])
def collector_cls(request):
    return request.param


@pytest.fixture(params=[QueryBatchLimit, TimeLimit])
def limit_cls(request):
    return request.param


def limit_cls_and_name_to_id(fixture_value):
    return '{}-{}'.format(fixture_value[0].__name__, fixture_value[1])


@pytest.fixture(
    params=[
        (QueryBatchLimit, 'total'),
        (QueryBatchLimit, 'read'),
        (QueryBatchLimit, 'write'),
        (QueryBatchLimit, 'other'),
        (TimeLimit, 'total'),
    ], ids=limit_cls_and_name_to_id)
def limit_cls_and_name(request):
    yield request.param
