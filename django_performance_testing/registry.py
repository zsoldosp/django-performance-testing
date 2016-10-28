from collections import OrderedDict
from django.utils.module_loading import import_string
from django.utils import six


class UniqueNamedClassRegistry(object):
    def __init__(self, dotted_paths):
        self.name2cls = OrderedDict(
            (cls.__name__, cls)
            for cls in six.moves.map(self._to_cls, dotted_paths)
        )

    def _to_cls(self, dotted_path):
        return import_string(dotted_path)
