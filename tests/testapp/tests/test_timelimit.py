from django_performance_testing.timing import \
    TimeCollector, TimeLimit


def test_it_has_the_correct_collector():
    assert TimeLimit.collector_cls == TimeCollector
