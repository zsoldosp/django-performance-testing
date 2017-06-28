from django.contrib.auth.models import Group
from django_performance_testing.reports import WorstReport
from django_performance_testing.signals import results_read
from testapp.test_helpers import WithId, run_testcases_with_django_runner
import pytest
import unittest


@pytest.fixture
def packaged_runner(db):
    class SampleTestCase(unittest.TestCase):

        def test_whatever_one(self):
            results_read.send(
                sender=WithId('whatever'), results=[1],
                context={'test': 'one'})

        def test_whatever_two(self):
            results_read.send(
                sender=WithId('whatever'), results=[2],
                context={'test': 'two'})

        def test_slow_query(self):
            list(Group.objects.all())

    def get_packaged_runner_with_options(options=None):
        options = options or {}
        return run_testcases_with_django_runner(SampleTestCase, nr_of_tests=3,
                                                runner_options=options)
    return get_packaged_runner_with_options


def test_runner_has_worst_report_attribute(packaged_runner):
    test_run = packaged_runner()
    assert isinstance(test_run["runner"].djpt_worst_report, WorstReport)


def test_report_is_printed_after_test_is_run(packaged_runner):
    test_run = packaged_runner()
    assert test_run["output"].endswith(
        test_run["runner"].djpt_worst_report.rendered())


def test_no_report_is_printed_with_print_report_set_to_false(
        packaged_runner, settings):
    settings.DJPT_PRINT_WORST_REPORT = False
    test_run = packaged_runner()
    assert "Worst Performing Items" not in test_run["output"]


def test_after_running_django_testcases_report_is_printed(packaged_runner):
    whatever = get_report_value_for(packaged_runner(), 'whatever', '')
    assert whatever.value == 2
    assert whatever.context == {'test': 'two'}


def test_has_worst_test_method_in_the_report(packaged_runner):
    report_data = get_report_data(packaged_runner())
    assert 'test method' in report_data


def get_report_value_for(test_run, heading, item_name):
    report_data = get_report_data(test_run)
    assert heading in list(report_data.keys())
    return report_data[heading]['type name'][item_name]


def get_report_data(test_run):
    return test_run["runner"].djpt_worst_report.data
