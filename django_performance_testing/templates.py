from django.template import Template
from .context import scoped_context
from .queries import QueryCollector, QueryBatchLimit
from .timing import TimeCollector, TimeLimit

try:
    orig_template_render
except NameError:
    orig_template_render = Template.render

id_ = 'Template.render'
querycount_collector = QueryCollector(id_=id_)
querycount_limit = QueryBatchLimit(collector_id=id_, settings_based=True)

time_collector = TimeCollector(id_=id_)
time_limit = TimeLimit(collector_id=id_, settings_based=True)


def template_render_that_fails_for_too_many_queries(template_self, *a, **kw):
    with scoped_context(key='template', value=template_self.name):
        with querycount_collector:
            with time_collector:
                return orig_template_render(template_self, *a, **kw)


def integrate_into_django_templates():
    Template.render = template_render_that_fails_for_too_many_queries
