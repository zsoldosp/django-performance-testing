import pytest
from django.utils import six
from django_performance_testing.core import NameValueResult
from django_performance_testing.reports import WorstReport, Result
from django_performance_testing.signals import results_collected
from testapp.test_helpers import WithId, FakeSender


def test_has_worst_value_and_its_context():
    report = WorstReport()
    results_collected.send(
        sender=WithId('id'), results=[4], context={'first': 'context'})
    assert len(report.data) == 1
    assert (4, {'first': 'context'}) == get_value_and_context(report, 'id')
    results_collected.send(
        sender=WithId('id'), results=[7], context={'2nd': 'context'})
    assert len(report.data) == 1
    assert (7, {'2nd': 'context'}) == get_value_and_context(report, 'id')
    results_collected.send(
        sender=WithId('id'), results=[5], context={'3rd': 'context'})
    assert len(report.data) == 1
    assert (7, {'2nd': 'context'}) == get_value_and_context(report, 'id')


def test_has_copy_of_the_context():
    report = WorstReport()
    sent_context = {'sent': 'context'}
    results_collected.send(
        sender=WithId('foo'), results=[4], context=sent_context)
    assert len(report.data) == 1
    r_val, r_context = get_value_and_context(report, 'foo')
    assert r_context == {'sent': 'context'}
    assert id(r_context) != id(sent_context)
    sent_context['another'] = 'entry'
    assert r_context == {'sent': 'context'}


def test_handles_multiple_sender_ids_as_separate_items():
    report = WorstReport()
    results_collected.send(
        sender=WithId('id one'), results=['a'], context={'context': 'one'})
    results_collected.send(
        sender=WithId('id two'), results=['z'], context={'context': 'two'})
    assert len(report.data) == 2
    assert ('a', {'context': 'one'}) == get_value_and_context(report, 'id one')
    assert ('z', {'context': 'two'}) == get_value_and_context(report, 'id two')


def test_result_repr_is_human_readable():
    result = Result(value='val', context={'foo': 'bar', 'baz': 4})
    assert 'val {\'baz\': 4, \'foo\': \'bar\'}' == repr(result)
    result = Result(
        value=(1, 2), context=dict((i, 'a'*i*10) for i in range(4)))
    lines = [
        '{0: \'\',',
        ' 1: \'{}\','.format('a'*10),
        ' 2: \'{}\','.format('a'*20),
        ' 3: \'{}\'}}'.format('a'*30),
    ]
    assert '(1, 2) {}'.format('\n'.join(lines)) == repr(result)


expected_report_data = """
Worst Performing Items

id 1:
=====
  querycount:
    two: 2
      test: some.app.tests.TestCase.test_foo
id 2:
=====
  querycount:
    nine: 9
      foo: bar
""".strip()


def test_report_printed_includes_all_needed_data():
    report = WorstReport()
    report.handle_results_collected(
        signal=None, sender=FakeSender('id 2', 'querycount'),
        results=[
            NameValueResult(name='nine', value=9)], context={'foo': 'bar'})
    report.handle_results_collected(
        signal=None, sender=FakeSender('id 1', 'querycount'),
        results=[NameValueResult(name='two', value=2)],
        context={'test': 'some.app.tests.TestCase.test_foo'})
    stream = six.StringIO()
    report.render(stream)
    assert stream.getvalue().strip() == expected_report_data


def test_report_prints_nothing_when_there_is_no_data():
    report = WorstReport()
    stream = six.StringIO()
    report.render(stream)
    assert stream.getvalue() == ''


def test_report_can_deal_with_single_anonymous_result_not_with_more():
    report = WorstReport()
    report.handle_results_collected(
        signal=None, sender=WithId('foo'),
        results=[9], context={})
    assert list(report.data.keys()) == ['foo']
    assert get_value_and_context(report, 'foo')[0] == 9
    with pytest.raises(TypeError) as excinfo:
        report.handle_results_collected(
            signal=None, sender=WithId('foo'),
            results=[1, 2], context={})
    assert 'Duplicate result name(s): \'\'' == str(excinfo.value)
    assert list(report.data.keys()) == ['foo']
    assert get_value_and_context(report, 'foo')[0] == 9


def test_there_is_one_channel_per_each_name_received():
    report = WorstReport()
    report.handle_results_collected(
        signal=None, sender=WithId('id'),
        results=[
            NameValueResult('one', 1), NameValueResult('two', 2)], context={})
    assert list(report.data.keys()) == ['id']
    assert get_tp_names(report, 'id') == ['one', 'two']
    assert (1, {}) == get_value_and_context(report, 'id', tp='one')
    assert (2, {}) == get_value_and_context(report, 'id', tp='two')


def test_has_separate_context_for_each_channels_worst():
    report = WorstReport()
    report.handle_results_collected(
        signal=None, sender=WithId('id'),
        results=[NameValueResult('one', 1), NameValueResult('two', 2)],
        context={'event': 'first'})
    report.handle_results_collected(
        signal=None, sender=WithId('id'),
        results=[NameValueResult('one', 3), NameValueResult('two', 1)],
        context={'event': 'second'})
    assert list(report.data.keys()) == ['id']
    assert get_tp_names(report, 'id') == ['one', 'two']
    assert (3, {'event': 'second'}) == \
        get_value_and_context(report, 'id', tp='one')
    assert (2, {'event': 'first'}) == \
        get_value_and_context(report, 'id', tp='two')


def test_has_separate_section_for_each_sender_type():
    report = WorstReport()
    report.handle_results_collected(
        signal=None, sender=FakeSender('id', 'type one'),
        results=[NameValueResult('count', 1)], context={'event': 'first'})
    report.handle_results_collected(
        signal=None, sender=FakeSender('id', 'type two'),
        results=[NameValueResult('count', 3)], context={'event': 'second'})
    assert list(report.data.keys()) == ['id']
    assert get_type_names(report, 'id') == ['type one', 'type two']
    assert (1, {'event': 'first'}) == \
        get_value_and_context(report, 'id', 'type one', 'count')
    assert (3, {'event': 'second'}) == \
        get_value_and_context(report, 'id', 'type two', 'count')


def get_value_and_context(report, id_, type_name='type name', tp=''):
    r = report.data[id_][type_name][tp]
    return r.value, r.context


def get_tp_names(report, id_, type_name='type name'):
    return sorted(report.data[id_][type_name].keys())


def get_type_names(report, id_):
    return sorted(report.data[id_].keys())
