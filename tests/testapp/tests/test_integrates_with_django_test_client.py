import pytest
from django.conf.urls import url
from django.contrib.auth.models import Group
from django.core.urlresolvers import reverse
from django.http import HttpResponse
from django_performance_testing.core import LimitViolationError

urlpatterns = []



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

    def run_n_queries_view(request):
        for i in range(kwparams['queries']):
            list(Group.objects.all())
        return HttpResponse()
    # client.get('test-view') would fail 'coz it's /test-view
    urlpatterns.append(url('test-view', run_n_queries_view, {}, 'test_view'))
    path = reverse('test_view')
    with pytest.raises(LimitViolationError) as excinfo:
        response = getattr(client, kwparams['method'].lower())(path)
        print(response.status_code)  # helps when it fails
    assert excinfo.value.context == {
        'Client.request': ['{method} {url}'.format(url=path, **kwparams)]}
