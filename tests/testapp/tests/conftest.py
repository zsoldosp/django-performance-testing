import pytest
from django_performance_testing.queries import QueryCollector, QueryBatchLimit
from django_performance_testing.timing import TimeCollector


@pytest.fixture(params=[QueryCollector, TimeCollector])
def collector_cls(request):
    return request.param


@pytest.fixture(params=[QueryBatchLimit])
def limit_cls(request):
    return request.param
