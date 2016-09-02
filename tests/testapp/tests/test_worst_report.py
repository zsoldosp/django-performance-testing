from django.utils import six
from django_performance_testing.signals import result_collected
from django_performance_testing.reports import WorstReport, Result
from testapp.test_helpers import WithId


def test_has_worst_value_and_its_context():
    report = WorstReport()
    result_collected.send(
        sender=WithId('id'), result=4, context={'first': 'context'})
    assert len(report.data) == 1
    assert report.data['id'].value == 4
    assert report.data['id'].context == {'first': 'context'}
    result_collected.send(
        sender=WithId('id'), result=7, context={'2nd': 'context'})
    assert len(report.data) == 1
    assert report.data['id'].value == 7
    assert report.data['id'].context == {'2nd': 'context'}
    result_collected.send(
        sender=WithId('id'), result=5, context={'3rd': 'context'})
    assert len(report.data) == 1
    assert report.data['id'].value == 7
    assert report.data['id'].context == {'2nd': 'context'}


def test_has_copy_of_the_context():
    report = WorstReport()
    sent_context = {'sent': 'context'}
    result_collected.send(
        sender=WithId('foo'), result=4, context=sent_context)
    assert len(report.data) == 1
    assert report.data['foo'].context == {'sent': 'context'}
    assert id(report.data['foo'].context) != id(sent_context)
    sent_context['another'] = 'entry'
    assert report.data['foo'].context == {'sent': 'context'}


def test_handles_multiple_sender_ids_as_separate_items():
    report = WorstReport()
    result_collected.send(
        sender=WithId('id one'), result='a', context={'context': 'one'})
    result_collected.send(
        sender=WithId('id two'), result='z', context={'context': 'two'})
    assert len(report.data) == 2
    assert report.data['id one'].value == 'a'
    assert report.data['id one'].context == {'context': 'one'}
    assert report.data['id two'].value == 'z'
    assert report.data['id two'].context == {'context': 'two'}


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


def test_report_printed_includes_all_needed_data():
    report = WorstReport()
    report.handle_result_collected(
        signal=None, sender=WithId('id 2 - querycount'),
        result=9, context={'foo': 'bar'})
    report.handle_result_collected(
        signal=None, sender=WithId('id 1 - querycount'),
        result=2, context={'test': 'some.app.tests.TestCase.test_foo'})
    stream = six.StringIO()
    report.render(stream)
    lines = stream.getvalue().strip().split('\n')
    assert len(lines) == 3
    assert lines[0] == 'Worst Performing Items'
    assert lines[1] == \
        "id 1 - querycount: 2 {'test': 'some.app.tests.TestCase.test_foo'}"
    assert lines[2] == "id 2 - querycount: 9 {'foo': 'bar'}"


def test_report_prints_nothing_when_there_is_no_data():
    report = WorstReport()
    stream = six.StringIO()
    report.render(stream)
    assert stream.getvalue() == ''
