from collections import OrderedDict
from django.conf import settings
from django.utils.module_loading import import_string
from django.utils import six


class DuplicateNamesError(TypeError):
    pass


class UniqueNamedClassRegistry(object):
    def __init__(self, dotted_paths):
        self._build_name2cls(dotted_paths)

    def _build_name2cls(self, dotted_paths):
        self.name2cls = OrderedDict(
            (cls.__name__, cls)
            for cls in six.moves.map(self._to_cls, dotted_paths)
        )
        if len(self.name2cls) != len(dotted_paths):
            raise DuplicateNamesError()

    def _to_cls(self, dotted_path):
        return import_string(dotted_path)


class SettingsOrDefaultBasedRegistry(UniqueNamedClassRegistry):

    settings_name = 'DJPT_KNOWN_LIMITS_DOTTED_PATHS'

    defaults = (
        'django_performance_testing.queries.QueryBatchLimit',
        'django_performance_testing.timing.TimeLimit',
    )

    def __init__(self):
        super(SettingsOrDefaultBasedRegistry, self).__init__(
            self.dotted_paths_for_init)

    @property
    def dotted_paths_for_init(self):
        if not hasattr(settings, self.settings_name):
            return self.defaults
        return getattr(settings, self.settings_name)
