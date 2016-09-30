from django_performance_testing.reports import WorstReport
from django_performance_testing.signals import results_collected
from testapp.test_helpers import WithId, run_testcase_with_django_runner
import unittest


def test_after_running_django_testcases_report_is_printed():

    class SampleTestCase(unittest.TestCase):

        def test_one(self):
            results_collected.send(
                sender=WithId('whatever'), results=[1],
                context={'test': 'one'})

        def test_two(self):
            results_collected.send(
                sender=WithId('whatever'), results=[2],
                context={'test': 'two'})
    test_run = run_testcase_with_django_runner(SampleTestCase, nr_of_tests=2)

    # actual test assertions
    test_runner = test_run['test_runner']
    assert isinstance(test_runner.djpt_worst_report, WorstReport)
    report_data = test_runner.djpt_worst_report.data
    assert 'whatever' in list(report_data.keys())
    whatever = report_data['whatever']['']
    assert whatever.value == 2
    assert whatever.context == {'test': 'two'}
    printed = test_run['out']
    assert printed.endswith(test_runner.djpt_worst_report.rendered())
