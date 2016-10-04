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

        def get_data(*parts):
            d = self.data
            for p in parts:
                d.setdefault(p, {})
                d = d[p]
            return d

        def handle_result(name, result):
            d = get_data(sender.id_, sender.type_name)
            current = d.get(name, None)
            if current is None or current.value < result:
                d[name] = Result(value=result, context=copy.deepcopy(context))

        for name, result in name_value_pairs:
            handle_result(name, result)

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
        stream.write('\nWorst Performing Items\n\n')
        self.render_dict(stream=stream, d=self.data, indent=0, underline='=')

    def render_dict(self, stream, d, indent, underline=None):
        prefix = ' '*indent

        for k in sorted(d.keys()):
            v = d[k]
            val, nextdict = self._to_val_nextdict(v)

            if val:
                val = ' {}'.format(val)
            else:
                val = ''
            line = '{}{}:{}'.format(prefix, k, val)
            stream.write('{}\n'.format(line))
            if underline:
                stream.write('{}\n'.format(underline*len(line)))
            if nextdict:
                self.render_dict(stream=stream, d=nextdict, indent=indent + 2)

    def _to_val_nextdict(self, v):
        if isinstance(v, Result):
            return (v.value, v.context)
        elif isinstance(v, dict):
            return (None, v)
        else:
            return (v, None)

    def rendered(self):
        out = six.StringIO()
        self.render(out)
        return out.getvalue()
