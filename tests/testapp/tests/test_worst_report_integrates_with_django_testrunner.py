from django.contrib.auth.models import Group
from django.utils import six
from django_performance_testing.management.commands.djpt_worst_report \
    import Command as WorstReportCommand
from django_performance_testing.signals import results_collected
from testapp.test_helpers import WithId, run_testcases_with_django_runner
import pytest
import unittest


@pytest.fixture
def packaged_runner(db):
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

    def get_packaged_runner_with_options(options=None):
        options = options or {}
        return run_testcases_with_django_runner(SampleTestCase, nr_of_tests=3,
                                                runner_options=options)
    return get_packaged_runner_with_options


def test_notice_is_printed_on_how_to_get_the_worst_report_after_test_run(
        packaged_runner, settings):
    settings.DJPT_PRINT_WORST_REPORT = True
    test_run = packaged_runner()
    report = get_report_text()
    assert not test_run["output"].endswith(report)
    notice = 'To see the Worst Performing Items report, ' \
             'run manage.py djpt_worst_report'
    assert notice in test_run["output"]


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
    cmd = get_command_after_run()
    return cmd.report.data


def get_report_text():
    cmd = get_command_after_run()
    return cmd.stdout.getvalue()


def get_command_after_run():
    cmd = WorstReportCommand(stdout=six.StringIO())
    cmd.handle()
    return cmd
