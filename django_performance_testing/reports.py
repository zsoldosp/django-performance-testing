import copy
from django.utils import six
from django_performance_testing.signals import result_collected
import pprint


class Result(object):
    def __init__(self, value, context):
        self.value = value
        self.context = context

    def __repr__(self):
        return '{} {}'.format(self.value, pprint.pformat(self.context))


class WorstReport(object):

    def __init__(self):
        result_collected.connect(self.handle_result_collected)
        self.data = {}

    def handle_result_collected(self, signal, sender, result, context, **kw):
        current = self.data.get(sender.id_)
        if current is None or current.value < result:
            self.data[sender.id_] = Result(
                value=result, context=copy.deepcopy(context))

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
