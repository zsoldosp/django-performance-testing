import pytest
from django.conf.urls import url
from django.contrib.auth.models import Group
from django.core.urlresolvers import reverse
from django.http import HttpResponse
from django_performance_testing.core import LimitViolationError

urlpatterns = []


class RegisterSelfAsViewContextManager(object):

    reverse_name = 'test_view'

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


class DbQueriesView(RegisterSelfAsViewContextManager):

    def __init__(self, value):
        self.value = value

    def __call__(self, request):
        for i in range(self.value):
            list(Group.objects.all())
        return HttpResponse()


@pytest.mark.parametrize('method,limit,value', [
    ['GET', 4, 5], ['POST', 1, 2]
], ids=['GET', 'POST'])
@pytest.mark.urls(__name__)
def test_can_specify_limits_through_settings_for_django_test_client(
        db, settings, client, method, limit, value):
    settings.PERFORMANCE_LIMITS = {
        'django.test.client.Client': {
            'queries': {
                'total': limit
            }
        }
    }
    with DbQueriesView(value=value) as dqv:
        with pytest.raises(LimitViolationError) as excinfo:
            dqv.request(getattr(client, method.lower()))
        assert excinfo.value.context == {
            'Client.request': ['{method} {url}'.format(
                url=dqv.url, method=method)]}
        assert excinfo.value.items_name == 'queries'
