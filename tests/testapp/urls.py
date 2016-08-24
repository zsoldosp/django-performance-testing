from django.conf.urls import url
from testapp.views import number_of_queries_to_run_view


urlpatterns = [
    url(
        r'number_of_queries_to_run/(?P<nr_of_queries>\d+)',
        number_of_queries_to_run_view, {}, 'nr_of_queries_view'),
]
