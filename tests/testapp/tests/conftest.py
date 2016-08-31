import pytest
from django_performance_testing.queries import QueryCollector


@pytest.fixture(params=[QueryCollector])
def collector_cls(request):
    return request.param
