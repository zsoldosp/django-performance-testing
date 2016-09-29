import pytest
from django.conf.urls import url
from django.contrib.auth.models import Group
from django.core.urlresolvers import reverse
from django.http import HttpResponse
from django_performance_testing.core import LimitViolationError

urlpatterns = []


class DbQueriesView(object):

    reverse_name = 'test_view'

    def __init__(self, value):
        self.value = value

    def __call__(self, request):
        for i in range(self.value):
            list(Group.objects.all())
        return HttpResponse()

    def __enter__(self):
        urlpatterns.append(url(self.reverse_name, self, {}, self.reverse_name))
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        urlpatterns.pop()

    @property
    def url(self):
        return reverse(self.reverse_name)

    def request(self, method):
        response = method(self.url)
        print(response.status_code)  # helps when it fails
        return response


@pytest.mark.parametrize('kwparams', [
    {'method': 'GET', 'limit': 4, 'queries': 5},
    {'method': 'POST', 'limit': 1, 'queries': 2},
], ids=['GET', 'POST'])
@pytest.mark.urls(__name__)
def test_can_specify_limits_through_settings_for_django_test_client(
        db, settings, client, kwparams):
    settings.PERFORMANCE_LIMITS = {
        'django.test.client.Client': {
            'queries': {
                'total': kwparams['limit']
            }
        }
    }
    with DbQueriesView(value=kwparams['queries']) as dqv:
        with pytest.raises(LimitViolationError) as excinfo:
            dqv.request(getattr(client, kwparams['method'].lower()))
        assert excinfo.value.context == {
            'Client.request': ['{method} {url}'.format(
                url=dqv.url, **kwparams)]}
