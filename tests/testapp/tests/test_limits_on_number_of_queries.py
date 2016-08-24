from django.contrib.auth.models import Group
from django_performance_testing.queries import QueryCollector


def test_can_count_inserts(db):
    with QueryCollector() as qc:
        Group.objects.create(name='foo')
    assert len(qc.queries) == 1
