import pytest
from django.core.urlresolvers import reverse
from django_performance_testing.core import LimitViolationError


@pytest.mark.parametrize('kwparams', [
    {'method': 'GET', 'limit': 4, 'queries': 5},
    {'method': 'POST', 'limit': 1, 'queries': 2},
], ids=['GET', 'POST'])
def test_can_specify_limits_through_settings_for_django_test_client(
        db, settings, client, kwparams):
    settings.PERFORMANCE_LIMITS = {
        'django.test.client.Client': {
            'queries': {
                'total': kwparams['limit']
            }
        }
    }

    url = reverse(
        'nr_of_queries_view', kwargs={'nr_of_queries': kwparams['queries']})
    with pytest.raises(LimitViolationError) as excinfo:
        getattr(client, kwparams['method'].lower())(url)
    assert excinfo.value.context == {
        'Client.request': ['{method} {url}'.format(url=url, **kwparams)]}
