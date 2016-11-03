from django.contrib.auth.models import Group
from django_performance_testing.reports import WorstReport
from django_performance_testing.signals import results_collected
from testapp.test_helpers import WithId, RunnerFixture
import pytest
import unittest


@pytest.fixture
def make_runner(db):
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

    def make_runner_with_options(options=None):
        options = options or {}
        return RunnerFixture(SampleTestCase, nr_of_tests=3,
                             runner_options=options)
    return make_runner_with_options


def test_runner_has_worst_report_attribute(make_runner):
    runner_fixture = make_runner()
    runner_fixture.run()
    assert isinstance(runner_fixture.test_runner.djpt_worst_report,
                      WorstReport)


def test_report_is_printed_after_test_is_run(make_runner):
    runner_fixture = make_runner()
    _result, output = runner_fixture.run()
    assert output.endswith(
        runner_fixture.test_runner.djpt_worst_report.rendered())


def test_no_report_is_printed_with_print_report_set_to_false(make_runner):
    test_runner = make_runner({"print_report": False})
    _result, output = test_runner.run()
    assert output.find("Worst Performing Items") is -1, \
        "Output was: {}".format(output)


def test_after_running_django_testcases_report_is_printed(make_runner):
    whatever = get_report_value_for(make_runner(), 'whatever', '')
    assert whatever.value == 2
    assert whatever.context == {'test': 'two'}


def test_has_worst_test_method_in_the_report(make_runner):
    report_data = get_report_data(make_runner())
    assert 'test method' in report_data


def get_report_value_for(runner_fixture, heading, item_name):
    report_data = get_report_data(runner_fixture)
    assert heading in list(report_data.keys())
    return report_data[heading]['type name'][item_name]


def get_report_data(runner_fixture):
    runner_fixture.run()
    return runner_fixture.test_runner.djpt_worst_report.data
