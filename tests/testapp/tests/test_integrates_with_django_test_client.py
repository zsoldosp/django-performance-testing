import pytest
from django.core.urlresolvers import reverse


def test_can_specify_limits_through_settings_for_django_test_client(
        db, settings, client):
    settings.PERFORMANCE_LIMITS = {
        'django.test.client.Client': {'count_limit': 0}}
    with pytest.raises(ValueError) as excinfo:
        client.get(reverse('nr_of_queries_view', kwargs={'nr_of_queries': 1}))
    assert 'Too many (1) queries (limit: 0)' == str(excinfo.value)
