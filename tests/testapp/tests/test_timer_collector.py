from datetime import timedelta
from django_performance_testing.timing import TimeCollector
from freezegun import freeze_time
import pytest
from testapp.test_helpers import capture_result_collected


@pytest.mark.parametrize('seconds', [10, 5, 0.04])
def test_captures_and_measures_elapsed_time(seconds):
    with capture_result_collected() as captured:
        with freeze_time('2016-09-22 15:57:01') as frozen_time:
            with TimeCollector():
                frozen_time.tick(timedelta(seconds=seconds))
    assert len(captured.calls) == 1
    assert pytest.approx(seconds) == captured.calls[0]['results']
