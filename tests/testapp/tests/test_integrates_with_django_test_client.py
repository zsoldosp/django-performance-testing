import pytest
from django.core.urlresolvers import reverse
from django.db import reset_queries


@pytest.mark.parametrize('kwparams', [
    {'method': 'GET', 'limit': 4, 'queries': 5},
    {'method': 'POST', 'limit': 1, 'queries': 2},
], ids=['GET', 'POST'])
def test_can_specify_limits_through_settings_for_django_test_client(
        db, settings, client, kwparams):
    reset_queries()  # without this, things go wrong with counting
    settings.PERFORMANCE_LIMITS = {
        'django.test.client.Client': {'count_limit': kwparams['limit']}}

    url = reverse(
        'nr_of_queries_view', kwargs={'nr_of_queries': kwparams['queries']})
    with pytest.raises(ValueError) as excinfo:
        getattr(client, kwparams['method'].lower())(url)
    expected_error_message = \
        'Too many ({queries}) queries (limit: {limit}) ' \
        '{{\'Client.request\': [\'{method} {url}\']}}'.format(
            url=url,
            **kwparams
        )
    assert expected_error_message == str(excinfo.value)
