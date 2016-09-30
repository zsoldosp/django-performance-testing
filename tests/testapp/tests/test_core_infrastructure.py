import pytest
from django_performance_testing.core import \
    BaseLimit, BaseCollector, LimitViolationError, NameValueResult
from django_performance_testing.signals import results_collected
from testapp.sixmock import patch, Mock
from testapp.test_helpers import \
    override_current_context, capture_result_collected


class TestCollectors(object):

    def test_can_create_without_id(self, collector_cls):
        collector = collector_cls()
        assert collector.id_ is None

    def test_can_create_multiple_without_id(self, collector_cls):
        collector_one = collector_cls()
        assert collector_one.id_ is None
        collector_two = collector_cls()
        assert collector_two.id_ is None

    def test_when_it_is_deleted_its_id_is_freed(self, collector_cls):
        collector_one = collector_cls(id_='bar')
        del collector_one
        collector_two = collector_cls(id_='bar')
        assert collector_two.id_ == 'bar'

    def test_sends_a_signal_when_context_is_exited(self, collector_cls):
        with capture_result_collected() as captured:
            assert captured.calls == []
            with collector_cls():
                pass
            assert len(captured.calls) == 1
            with collector_cls():
                pass
            assert len(captured.calls) == 2

    def test_signal_passes_along_current_contexts_copy(self, collector_cls):
        with override_current_context() as ctx:
            ctx.enter(key='extra', value='context')
            with capture_result_collected() as captured:
                assert captured.calls == []
                with collector_cls() as collector:
                    pass
        assert len(captured.calls) == 1
        params = captured.calls[0]
        assert params['sender'] == collector
        received_context = params['context']
        assert received_context == {'extra': ['context']}
        assert received_context == ctx.data
        assert id(received_context) != id(ctx.data)
        assert received_context['extra'] == ctx.data['extra']
        assert id(received_context['extra']) != id(ctx.data['extra'])

    def test_signals_all_listeners_reports_first_failure(self, collector_cls):
        collector = collector_cls()

        class MyException(Exception):
            pass

        def get_mock_listener():
            m = Mock()
            m.return_value = None
            return m

        first_attached_handler = get_mock_listener()

        def second_handler_that_will_fail(*a, **kw):
            raise MyException('foo')
        last_attached_handler = get_mock_listener()

        listeners = [
            first_attached_handler, second_handler_that_will_fail,
            last_attached_handler]
        for l in listeners:
            results_collected.connect(l)
        try:
            with pytest.raises(MyException) as excinfo:
                with collector:
                    pass
            assert str(excinfo.value).endswith('foo')
            method_name_in_stacktrace = 'second_handler_that_will_fail'
            assert method_name_in_stacktrace in str(excinfo.value)
            assert first_attached_handler.called
            assert last_attached_handler.called
        finally:
            for l in listeners:
                results_collected.disconnect(l)

    def test_signal_handler_error_doesnt_hide_orig_error(self, collector_cls):
        collector = collector_cls()
        failing_signal_handler = Mock(side_effect=Exception('handler error'))
        results_collected.connect(failing_signal_handler)
        try:
            with pytest.raises(Exception) as excinfo:
                with collector:
                    raise Exception('actual code error')
            assert str(excinfo.value) == 'actual code error'
            assert failing_signal_handler.called
        finally:
            results_collected.disconnect(failing_signal_handler)


class TestLimits(object):
    def test_limit_knows_its_collector(self, limit_cls):
        assert hasattr(limit_cls, 'collector_cls')
        assert isinstance(limit_cls.collector_cls, type)

    def test_creating_with_id_doesnt_create_own_collector(self, limit_cls):
        collector = limit_cls.collector_cls(id_='bar')  # noqa: F841
        limit = limit_cls(collector_id='bar')
        assert limit.collector_id == 'bar'
        assert limit.collector is None

    def test_creating_without_id_creates_its_own_collector(self, limit_cls):
        limit = limit_cls()
        assert isinstance(limit.collector, limit_cls.collector_cls)
        assert limit.collector_id is None

    def test_it_is_a_properly_wired_up_base_limit(self, limit_cls):
        assert issubclass(limit_cls, BaseLimit)
        assert issubclass(limit_cls.collector_cls, BaseCollector)
        assert limit_cls.results_collected_handler == \
            BaseLimit.results_collected_handler
        assert hasattr(limit_cls, 'handle_results')
        assert callable(limit_cls.handle_results)
        assert hasattr(limit_cls, 'settings_key')
        assert isinstance(limit_cls.settings_key, str)

    def test_has_required_attrs_for_limit_violation_error(self, limit_cls):
        def assert_has_str_attr(name):
            assert hasattr(limit_cls, name)
            assert isinstance(getattr(limit_cls, name), str)

        assert_has_str_attr('quantifier')
        assert_has_str_attr('items_name')

    @pytest.mark.parametrize('limit,value', [
            (3, 2), (1, 0)
        ])
    def test_when_below_the_limit_there_is_no_error(
            self, limit_cls_and_name, limit, value):
        limit_cls, name = limit_cls_and_name
        assert limit > value, 'test pre-req'
        limit_obj = limit_cls(**{name: limit})
        limit_obj.handle_results(
            results=[NameValueResult(name, value)], context=None)
        assert True  # no exception raised

    @pytest.mark.parametrize('number', [9, 7])
    def test_when_exactly_limit_there_is_no_error(
            self, limit_cls_and_name, number):
        limit_cls, name = limit_cls_and_name
        limit_obj = limit_cls(**{name: number})
        limit_obj.handle_results(
            results=[NameValueResult(name, number)], context=None)
        assert True  # no exception raised

    @pytest.mark.parametrize('limit,value', [
            (1, 9), (9, 10)
        ])
    def test_when_above_the_limit_there_is_an_error(
            self, limit_cls_and_name, limit, value):
        limit_cls, name = limit_cls_and_name
        assert limit < value, 'test pre-req'
        limit_obj = limit_cls(**{name: limit})
        result = NameValueResult(name, value)
        with pytest.raises(LimitViolationError) as excinfo:
            limit_obj.handle_results(
                results=[result], context=None)
        assert excinfo.value.limit_obj == limit_obj
        assert excinfo.value.result == result
        assert excinfo.value.actual == str(value)
        assert not excinfo.value.context


class TestLimitsListeningOnSignals(object):

    def get_call_capturing_limit(self, limit_cls, **kw):

        class CallCapturingLimit(limit_cls):
            calls = []

            def handle_results(self, results, context):
                self.calls.append(
                    dict(results=results, context=context))

        return CallCapturingLimit(**kw)

    def test_listening_by_id_is_always_active(self, limit_cls):
        collector = limit_cls.collector_cls(id_='listen by id')
        limit = self.get_call_capturing_limit(
            limit_cls=limit_cls, collector_id='listen by id')
        results_collected.send(
            sender=collector, results=[0],
            context={'before': 'context manager'})
        with limit:
            results_collected.send(
                sender=collector, results=[1],
                context={'inside': 'context manager'})
        results_collected.send(
            sender=collector, results=[2],
            context={'after': 'context manager'})

        assert len(limit.calls) == 3
        assert limit.calls == [
            {'results': [0], 'context': {'before': 'context manager'}},
            {'results': [1], 'context': {'inside': 'context manager'}},
            {'results': [2], 'context': {'after': 'context manager'}},
        ]

    def test_without_id_only_listens_while_a_context_manager(self, limit_cls):
        limit = self.get_call_capturing_limit(limit_cls=limit_cls)
        assert limit.collector_id is None
        results_collected.send(
            sender=limit.collector, results=[0],
            context={'before': 'context manager'})
        with limit:
            results_collected.send(
                sender=limit.collector, results=[1],
                context={'inside': 'context manager'})
            assert len(limit.calls) == 1
            assert limit.calls == [
                {'results': [1], 'context': {'inside': 'context manager'}},
            ]
        limit.calls = []
        results_collected.send(
            sender=limit.collector, results=[2],
            context={'after': 'context manager'})
        assert len(limit.calls) == 0

    def test_only_listens_to_its_collector_named(self, limit_cls):
        listened_to = limit_cls.collector_cls(id_='has listener')
        unlistened = limit_cls.collector_cls(id_='no listeners')
        limit = self.get_call_capturing_limit(
            limit_cls=limit_cls, collector_id='has listener')
        results_collected.send(
            sender=listened_to, results=[5], context={'should': 'receive'})
        results_collected.send(
            sender=unlistened, results=[6], context={'not': 'received'})
        assert len(limit.calls) == 1
        assert limit.calls == [
            {'results': [5], 'context': {'should': 'receive'}},
        ]

    def test_only_listens_to_its_own_typed_collector(self, limit_cls):
        id_ = 'id to listen to'

        class OtherCollectorType(BaseCollector):
            pass

        listened_to = limit_cls.collector_cls(id_=id_)
        unlistened = OtherCollectorType(id_=id_)
        limit = self.get_call_capturing_limit(
            limit_cls=limit_cls, collector_id=id_)
        results_collected.send(
            sender=listened_to, results=[1], context={'should': 'receive'})
        results_collected.send(
            sender=unlistened, results=[2], context={'not': 'received'})
        assert len(limit.calls) == 1
        assert limit.calls == [
            {'results': [1], 'context': {'should': 'receive'}},
        ]

    def test_only_listens_to_its_collector_anonymous(self, limit_cls):
        limit = self.get_call_capturing_limit(limit_cls=limit_cls)
        listened_to = limit.collector
        unlistened = limit_cls.collector_cls(id_='no listeners')
        with limit:
            results_collected.send(
                sender=listened_to, results=[99],
                context={'should': 'receive'})
            results_collected.send(
                sender=unlistened, results=[55],
                context={'not': 'received'})
            assert len(limit.calls) == 1
            assert limit.calls == [
                {'results': [99], 'context': {'should': 'receive'}},
            ]

    def test_anonymous_enter_exit_calls_same_on_its_collector(self, limit_cls):
        limit = limit_cls()
        with patch.object(limit.collector, '__enter__') as enter_mock:
            with patch.object(limit.collector, '__exit__') as exit_mock:
                enter_mock.assert_not_called()
                exit_mock.assert_not_called()
                with limit:
                    enter_mock.assert_called_once_with()
                exit_mock.assert_called_once_with(None, None, None)

    def test_anonymous_quits_from_signal_after_collector_exit(self, limit_cls):
        limit = self.get_call_capturing_limit(limit_cls=limit_cls)
        with limit:
            pass
        assert len(limit.calls) == 1


class TestCreatingSettingsBasedLimits(object):

    def test_cannot_provide_both_data_and_settings_based_true(self, limit_cls):
        collector = limit_cls.collector_cls(id_='some id')  # noqa: F841
        with pytest.raises(TypeError) as excinfo:
            limit_cls(collector_id='some id', data={}, settings_based=True)
        assert 'Either provide data (kwargs) or settings_based, not both.' == \
            str(excinfo.value)
        with pytest.raises(TypeError) as excinfo:
            limit_cls(collector_id='some id', foo=1, settings_based=True)
        assert 'Either provide data (kwargs) or settings_based, not both.' == \
            str(excinfo.value)

    def test_values_based_on_setting_runtime_value(self, limit_cls, settings):
        id_ = 'runtime settings based limit'
        collector = limit_cls.collector_cls(id_=id_)  # noqa: F841
        limit = limit_cls(collector_id=id_, settings_based=True)
        settings.PERFORMANCE_LIMITS = {}
        assert limit.data == {}
        settings.PERFORMANCE_LIMITS = {
            id_: {limit_cls.settings_key: {'data': 'foo'}}
        }
        assert limit.data == {'data': 'foo'}
        settings.PERFORMANCE_LIMITS = {
            id_: {limit_cls.settings_key: {'whatever': 'bar'}}
        }
        assert limit.data == {'whatever': 'bar'}

    def test_when_providing_kwargs_data_that_is_obtained(self, limit_cls):
        collector = limit_cls.collector_cls(id_='kwarg data')  # noqa: F841
        limit = limit_cls(collector_id='kwarg data', foo='bar')
        assert limit.data == {'foo': 'bar'}

    def test_without_collector_id_cannot_be_settings_based(self, limit_cls):
        with pytest.raises(TypeError) as excinfo:
            limit_cls(settings_based=True)
        assert 'Can only be settings based when collector_id is provided.' == \
            str(excinfo.value)

    def test_when_no_data_in_settings_dont_fail(self, limit_cls, settings):
        id_ = 'settings has no value for this limit'
        collector = limit_cls.collector_cls(id_=id_)  # noqa: F841
        limit = limit_cls(collector_id=id_, settings_based=True)
        settings.PERFORMANCE_LIMITS = {}
        assert limit.data == {}
        limit.handle_results(
            results=[NameValueResult('total', 1)], context={})
        assert True  # no error is raised

    def test_correct_settings_data_gets_passed_on(self, limit_cls, settings):
        id_ = 'foo'
        random_str = 'bar'
        settings.PERFORMANCE_LIMITS = {
            id_: {
                limit_cls.settings_key + random_str: {
                    'bad': 'wrong second level id in P_L',
                },
                limit_cls.settings_key: {
                    'good': 'config'
                }
            },
            random_str: {
                limit_cls.settings_key + random_str: {
                    'bad': 'under wrong id in P_L',
                },
                limit_cls.settings_key: {
                    'bad': 'under wrong id in P_L'
                },
            }
        }
        limit = limit_cls(collector_id=id_, settings_based=True)
        assert limit.data == {'good': 'config'}


# TODO: what to do w/ reports, where one'd listen on more than one collector?
