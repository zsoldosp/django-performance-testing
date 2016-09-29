from datetime import timedelta
from django_performance_testing.core import LimitViolationError
from django_performance_testing.timing import \
    TimeCollector, TimeLimit
from freezegun import freeze_time
import pytest


def test_it_has_the_correct_collector():
    assert TimeLimit.collector_cls == TimeCollector


def test_it_has_the_correct_attributes_for_limitviolationerror():
    assert TimeLimit.quantifier == 'many'
    assert TimeLimit.items_name == 'elapsed seconds'


@pytest.mark.parametrize('seconds', [10.0, 5.0])
def test_can_limit_elapsed_seconds(seconds):
    with freeze_time('2016-09-22 15:57:01') as frozen_time:
        with pytest.raises(LimitViolationError) as excinfo:
            with TimeLimit(total=0):
                frozen_time.tick(timedelta(seconds=seconds))
    assert excinfo.value.base_error_msg == \
        'Too many ({}) total elapsed seconds (limit: 0)'.format(seconds)
