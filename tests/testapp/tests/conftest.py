import pytest
from django_performance_testing.queries import QueryCollector, QueryBatchLimit


@pytest.fixture(params=[QueryCollector])
def collector_cls(request):
    return request.param


@pytest.fixture(params=[QueryBatchLimit])
def limit_cls(request):
    return request.param
