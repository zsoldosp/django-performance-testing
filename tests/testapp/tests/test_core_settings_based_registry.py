from django_performance_testing.registry import \
    SettingsOrDefaultBasedRegistry, UniqueNamedClassRegistry
from testapp.sixmock import patch


class SODBRToTest(SettingsOrDefaultBasedRegistry):
    settings_name = 'DJPT_DOTTED_PATHS_FOR_TESTING'

    def __init__(self, defaults=None):
        if defaults is None:
            defaults = tuple()
        self.defaults = defaults
        patched = patch.object(
            UniqueNamedClassRegistry, '_build_name2cls', autospec=True)
        with patched as mock:
            self.uncr_init_name2cls_mock = mock
            super(SODBRToTest, self).__init__()


def test_settings_or_default_is_unique_named_class_regisry():
    assert issubclass(SettingsOrDefaultBasedRegistry, UniqueNamedClassRegistry)


def test_sanity_check_test_double(settings):
    assert not hasattr(settings, SODBRToTest.settings_name)
    default_defaults = SODBRToTest()
    default_defaults.uncr_init_name2cls_mock.assert_called_once_with(
        default_defaults, tuple())
    assert tuple() == default_defaults.dotted_paths_for_init
    vals = ('abc', 'def')
    default_from_args = SODBRToTest(vals)
    default_from_args.uncr_init_name2cls_mock.assert_called_once_with(
        default_from_args, vals)
    assert vals == default_from_args.dotted_paths_for_init


def test_when_no_settings_specified_defaults_are_used(settings):
    """
        'dupicate' of test_sanity_check_test_double as code goes,
        but not by intent, hence the separate test
    """
    assert not hasattr(settings, SODBRToTest.settings_name)
    vals = ('asd', '2asd')
    assert SODBRToTest(vals).dotted_paths_for_init == vals


def test_when_settings_exist_that_is_taken_and_default_is_ignored(settings):
    settings.DJPT_DOTTED_PATHS_FOR_TESTING = ('asd',)
    defaults = ('qwert',)
    assert settings.DJPT_DOTTED_PATHS_FOR_TESTING != defaults  # sanity check
    sut = SODBRToTest(defaults=defaults)
    assert sut.dotted_paths_for_init == settings.DJPT_DOTTED_PATHS_FOR_TESTING
