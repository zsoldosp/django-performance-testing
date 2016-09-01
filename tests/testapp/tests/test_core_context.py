import pytest
from django_performance_testing import context
Context = context.Context


class TestContext(object):

    def test_context_enter_adds_context_exit_removes(self):
        ctx = Context()
        assert ctx.data == {}
        ctx.enter(key='ctx key', value='ctx value')
        assert ctx.data == {'ctx key': ['ctx value']}
        ctx.exit(key='ctx key', value='ctx value')
        assert ctx.data == {}

    def test_exiting_a_not_entered_context_is_an_error(self):
        ctx = Context()
        with pytest.raises(ValueError) as excinfo:
            ctx.exit(key='no such key', value='some value')
        assert str(excinfo.value) == \
            'cannot exit not entered context - key {!r} mismatch'.format(
                'no such key')

        ctx.enter(key='key', value='enter value')
        with pytest.raises(ValueError) as excinfo:
            ctx.exit(key='key', value='exit value')
        assert str(excinfo.value) == \
            'cannot exit not entered context - value mismatch ' \
            '(exit: {!r}, enter: {!r})'.format(
                'exit value', 'enter value')

    def test_can_enter_for_same_key_multiple_times(self):
        """ think e.g.: client redirect following """
        ctx = Context()
        ctx.enter(key='key', value='first')
        ctx.enter(key='key', value='second')
        assert ctx.data == {'key': ['first', 'second']}

    def test_multiple_values_for_key_must_be_exited_in_reverse_order(self):
        ctx = Context()
        ctx.enter(key='foo', value=1)
        ctx.enter(key='foo', value=2)
        with pytest.raises(ValueError) as excinfo:
            ctx.exit(key='foo', value=1)
        assert str(excinfo.value) == \
            'cannot exit not entered context - value mismatch ' \
            '(exit: 1, enter: 2)'

    def test_there_is_a_singleton_current(self):
        assert isinstance(context.current, Context)
