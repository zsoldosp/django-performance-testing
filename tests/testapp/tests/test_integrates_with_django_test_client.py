from datetime import timedelta
from django.conf.urls import url
from django.contrib.auth.models import Group
from django.core.urlresolvers import reverse
from django.http import HttpResponse
from django_performance_testing.core import LimitViolationError
from freezegun import freeze_time
import pytest

urlpatterns = []


class RegisterSelfAsViewContextManager(object):

    reverse_name = 'test_view'

    def __init__(self, value):
        self.value = value

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

    def __call__(self, request):
        for i in range(self.value):
            list(Group.objects.all())
        return HttpResponse()


class SlowRenderingView(RegisterSelfAsViewContextManager):

    def __enter__(self):
        self.frozen_time_ctx = freeze_time('2016-09-29 18:18:01')
        self.frozen_time = self.frozen_time_ctx.__enter__()
        return super(SlowRenderingView, self).__enter__()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.frozen_time_ctx.__exit__(exc_type, exc_val, exc_tb)
        return super(SlowRenderingView, self).__exit__(
            exc_type, exc_val, exc_tb)

    def __call__(self, request):
        self.frozen_time.tick(timedelta(seconds=self.value))
        return HttpResponse()


@pytest.mark.parametrize('method,limit,value,cfg_key,items_name,view_ctx', [
    ['GET', 4, 5, 'queries', 'queries', DbQueriesView],
    ['POST', 1, 2, 'queries', 'queries', DbQueriesView],
    ['GET', 4, 5, 'time', 'elapsed seconds', SlowRenderingView],
    ['POST', 1, 2, 'time', 'elapsed seconds', SlowRenderingView],
])
@pytest.mark.urls(__name__)
def test_can_specify_limits_through_settings_for_django_test_client(
        db, settings, client, method, limit, value, cfg_key, items_name,
        view_ctx):
    settings.PERFORMANCE_LIMITS = {
        'django.test.client.Client': {
            cfg_key: {
                'total': limit
            }
        }
    }
    with view_ctx(value=value) as vctx:
        with pytest.raises(LimitViolationError) as excinfo:
            vctx.request(getattr(client, method.lower()))
        assert excinfo.value.context == {
            'Client.request': ['{method} {url}'.format(
                url=vctx.url, method=method)]}
        assert excinfo.value.items_name == items_name, \
            excinfo.value.base_error_msg
