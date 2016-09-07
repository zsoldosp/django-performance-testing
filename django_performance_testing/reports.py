import copy
from django.utils import six
from django_performance_testing.signals import results_collected
import pprint


class Result(object):
    def __init__(self, value, context):
        self.value = value
        self.context = context

    def __repr__(self):
        return '{} {}'.format(self.value, pprint.pformat(self.context))


class WorstReport(object):

    def __init__(self):
        results_collected.connect(self.handle_results_collected)
        self.data = {}

    def handle_results_collected(self, signal, sender, results, context, **kw):
        name_value_pairs = list(map(self.to_name_value_pair, results))
        self.ensure_unique_names(name_value_pairs)
        current = self.data.get(sender.id_, {}).get('')
        result = results[0]
        if current is None or current.value < result:
            self.data[sender.id_] = {
                '': Result(value=result, context=copy.deepcopy(context))
            }

    def to_name_value_pair(self, value):
        return (
            getattr(value, 'name', ''),
            getattr(value, 'value', value)
        )

    def ensure_unique_names(self, name_value_pairs):
        dupes = set()
        last = None
        for (name, value) in sorted(name_value_pairs):
            if name == last:
                dupes.add(name)
            last = name
        if dupes:
            dupes_as_str = ', '.join(map(repr, dupes))
            raise TypeError(
                'Duplicate result name(s): {}'.format(dupes_as_str))

    def render(self, stream):
        if not self.data:
            return
        stream.write('Worst Performing Items\n')
        for k in sorted(self.data.keys()):
            stream.write('{}: {}\n'.format(k, self.data[k]))

    def rendered(self):
        out = six.StringIO()
        self.render(out)
        return out.getvalue()
