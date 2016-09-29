import pytest
from django.utils import six
from django_performance_testing.core import LimitViolationError
from testapp.sixmock import MagicMock, PropertyMock


def test_required_arguments():
    code = LimitViolationError.__init__.__code__
    assert ('self', 'limit_obj', 'result', 'context', 'tb') == \
        code.co_varnames[:code.co_argcount]


def get_mocked_properties(**kwargs):
    mock = MagicMock()
    for (k, v) in six.iteritems(kwargs):
        setattr(type(mock), k, PropertyMock(return_value=v))
    return mock


def get_mocked_properties_lve(limit_kwargs=None, result_kwargs=None,
                              context=None):
    if limit_kwargs is None:
        limit_kwargs = {}
    if result_kwargs is None:
        result_kwargs = {}
    limit = get_mocked_properties(**limit_kwargs)
    result = get_mocked_properties(**result_kwargs)
    return LimitViolationError(limit_obj=limit, result=result, context=context)


@pytest.mark.parametrize('val', ['foo', 'bar', 'baz'])
def test_quantifier_comes_from_limit(val):
    lve = get_mocked_properties_lve(limit_kwargs={'quantifier': val})
    assert lve.quantifier == val


@pytest.mark.parametrize('val', ['foo', 'bar', 'baz'])
def test_items_name_comes_from_limit(val):
    lve = get_mocked_properties_lve(limit_kwargs={'items_name': val})
    assert lve.items_name == val


@pytest.mark.parametrize('val,expected', [
    ('foo', ' (for foo)'),
    ('bar', ' (for bar)'),
    ('baz', ' (for baz)'),
    (None, ''),
])
def test_collector_id_text_comes_from_limit(val, expected):
    lve = get_mocked_properties_lve(limit_kwargs={'collector_id': val})
    lve.limit_obj.is_anonymous.return_value = val is None
    assert lve.collector_text == expected


@pytest.mark.parametrize('val', ['foo', 'bar', 'baz'])
def test_name_comes_from_result(val):
    lve = get_mocked_properties_lve(result_kwargs={'name': val})
    assert lve.name == val


@pytest.mark.parametrize('val', ['foo', 'bar', 'baz'])
def test_actual_comes_from_result(val):
    lve = get_mocked_properties_lve()
    lve.result.__str__.return_value = val
    assert lve.actual == val


@pytest.mark.parametrize('val', ['foo', 'bar', 'baz'])
def test_limit_value_comes_from_method_call_on_limit_with_result(val):
    lve = get_mocked_properties_lve(result_kwargs={'name': val})
    lve.limit_obj.reset_mock()
    lve.limit_obj.limit_for.return_value = 1
    assert lve.limit == 1
    lve.limit_obj.limit_for.assert_called_once_with(lve.result)


def test_context_comes_from_instance_context():
    context = {}
    lve = LimitViolationError(
        limit_obj=MagicMock(), result=MagicMock(), context=context)
    assert id(lve.context) == id(context)


def test_error_message_is_rendered_from_the_properties_no_ctx_no_tb():
    class FakeLimitViolationError(LimitViolationError):

        quantifier = 'many'
        items_name = 'queries'
        name = 'read'
        collector_text = ' (for collector_id)'
        actual = '4'
        limit = '3'

    lve = FakeLimitViolationError(
        limit_obj=MagicMock(), result=MagicMock(), context=None)
    assert lve.base_error_msg == \
        'Too many (4) read queries (for collector_id) (limit: 3)'


@pytest.mark.parametrize(
    'context,expected_repr', [
        ({'a': 1, 'b': 2, 'c': 3}, "{'a': 1, 'b': 2, 'c': 3}"),
        ({'foo': 'bar', 'bar': 'baz'}, "{'bar': 'baz', 'foo': 'bar'}"),
        ({}, '')
    ]
)
def test_if_context_is_given_its_turned_to_repr(context, expected_repr):
    lve = LimitViolationError(
        limit_obj=MagicMock(), result=MagicMock(), context=context)
    assert lve.context_repr == expected_repr


@pytest.mark.parametrize(
    'val,expected', [
        ('foo', 'foo'),
        ('bar', 'bar'),
        ('baz', 'baz'),
        (None, ''),
    ]
)
def test_if_traceback_is_given_its_stored(val, expected):
    lve = LimitViolationError(
        limit_obj=MagicMock(), result=MagicMock(), context=None, tb=val)
    assert lve.tb_msg == expected


@pytest.mark.parametrize(
    'base_msg,ctx_msg, tb, expected', [
        ('base', 'ctx', 'tb', 'base ctx\ntb'),
        ('base foo', 'base ctx', 'base tb', 'base foo base ctx\nbase tb'),
        ('bar', '', 'bar tb', 'bar\nbar tb'),
        ('baz', 'baz ctx', '', 'baz baz ctx'),
    ]
)
def test_full_error_message_is_built_from_properties(
        base_msg, ctx_msg, tb, expected):
    class FakeLimitViolationError(LimitViolationError):

        base_error_msg = base_msg
        context_repr = ctx_msg
        tb_msg = tb

    lve = FakeLimitViolationError(
        limit_obj=MagicMock(), result=MagicMock(), context=None)
    assert lve.error_msg == expected


@pytest.mark.parametrize('val', ['foo', 'bar', 'baz'])
def test_actual_exception_message_is_derived_from_error_msg_property(val):
    class FakeLimitViolationError(LimitViolationError):

        error_msg = val

    lve = FakeLimitViolationError(
        limit_obj=MagicMock(), result=MagicMock(), context=None)
    assert str(lve) == val


@pytest.mark.parametrize('val', ['foo', 'bar', 'baz'])
def test_clone_with_more_info_preserves_orig_arguments(val):
    context = {}
    lve = LimitViolationError(
        limit_obj=MagicMock(), result=MagicMock(), context=context)
    cloned_lve = lve.clone_with_more_info(orig_tb='foo')
    assert id(cloned_lve.context) == id(lve.context)
    assert id(cloned_lve.limit_obj) == id(lve.limit_obj)
    assert id(cloned_lve.result) == id(lve.result)
    assert cloned_lve.tb == 'foo'
