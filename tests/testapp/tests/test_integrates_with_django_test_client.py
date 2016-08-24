import pprint
import pytest
from django.core.urlresolvers import reverse


@pytest.mark.parametrize('kwparams', [
    {'method': 'get', 'limit': 4, 'queries': 5},
    {'method': 'post', 'limit': 1, 'queries': 2},
], ids=['get', 'post'])
def test_can_specify_limits_through_settings_for_django_test_client(
        db, settings, client, kwparams):
    from django.db import reset_queries
    reset_queries()  # without this, things go wrong with counting
    settings.PERFORMANCE_LIMITS = {
        'django.test.client.Client': {'count_limit': kwparams['limit']}}

    url = reverse(
        'nr_of_queries_view', kwargs={'nr_of_queries': kwparams['queries']})
    with pytest.raises(ValueError) as excinfo:
        getattr(client, kwparams['method'])(url)
    expected_error_message = 'Too many ({}) queries (limit: {}) {}'.format(
        kwparams['queries'], kwparams['limit'],
        pprint.pformat({'Client.{}'.format(kwparams['method'].upper()): url}))
    assert expected_error_message == str(excinfo.value)
