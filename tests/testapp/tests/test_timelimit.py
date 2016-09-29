from django_performance_testing.timing import \
    TimeCollector, TimeLimit


def test_it_has_the_correct_collector():
    assert TimeLimit.collector_cls == TimeCollector


def test_it_has_the_correct_attributes_for_limitviolationerror():
    assert TimeLimit.quantifier == 'many'
    assert TimeLimit.items_name == 'elapsed seconds'
