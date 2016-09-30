from django.contrib.auth.models import Group
from django_performance_testing.reports import WorstReport
from django_performance_testing.signals import results_collected
from testapp.test_helpers import WithId, run_testcase_with_django_runner
import pytest
import unittest


@pytest.fixture
def sample_test_results(db):
    class SampleTestCase(unittest.TestCase):

        def test_whatever_one(self):
            results_collected.send(
                sender=WithId('whatever'), results=[1],
                context={'test': 'one'})

        def test_whatever_two(self):
            results_collected.send(
                sender=WithId('whatever'), results=[2],
                context={'test': 'two'})

        def test_slow_query(self):
            list(Group.objects.all())

    return run_testcase_with_django_runner(SampleTestCase, nr_of_tests=3)


def test_runner_has_worst_report_attribute(sample_test_results):
    test_runner = sample_test_results['test_runner']
    assert isinstance(test_runner.djpt_worst_report, WorstReport)


def test_report_is_printed_after_test_is_run(sample_test_results):
    test_runner = sample_test_results['test_runner']
    printed = sample_test_results['out']
    assert printed.endswith(test_runner.djpt_worst_report.rendered())


def test_after_running_django_testcases_report_is_printed(sample_test_results):
    whatever = get_report_value_for(sample_test_results, 'whatever', '')
    assert whatever.value == 2
    assert whatever.context == {'test': 'two'}


def test_has_worst_test_method_in_the_report(sample_test_results):
    report_data = get_report_data(sample_test_results)
    assert sorted(['write', 'read', 'other', 'total']) == \
        sorted(report_data['test method'].keys())
    worst_total_tm = get_report_value_for(
        sample_test_results, 'test method', 'total')
    assert len(worst_total_tm.context) == 1
    worst_test = worst_total_tm.context['test name']
    assert len(worst_test) == 1
    assert worst_test[0].startswith(
        'test_slow_query ({}'.format(__name__))
    assert worst_test[0].endswith('.SampleTestCase)')


def get_report_value_for(sample_test_results, heading, item_name):
    report_data = get_report_data(sample_test_results)
    assert heading in list(report_data.keys())
    return report_data[heading][item_name]


def get_report_data(sample_test_results):
    test_runner = sample_test_results['test_runner']
    return test_runner.djpt_worst_report.data
