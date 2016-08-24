from django.conf.urls import patterns, url
from testapp.views import number_of_queries_to_run_view


urlpatterns = patterns(
    'testapp',
    url(
        r'number_of_queries_to_run/(?P<nr_of_queries>\d+)',
        number_of_queries_to_run_view, {}, 'nr_of_queries_view'),
)
