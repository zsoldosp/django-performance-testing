from datetime import timedelta
from django.contrib.auth.models import Group
from django.template import loader
from django_performance_testing.core import LimitViolationError
import pytest
from freezegun import freeze_time


def test_has_support_for_number_of_queries_in_templates(db, settings):
    settings.PERFORMANCE_LIMITS = {
        'Template.render': {
            'queries': {
                'total': 0
            }
        }
    }
    template = loader.get_template('all-group-names.markdown')
    with pytest.raises(LimitViolationError) as excinfo:
        template.render(context={'groups': Group.objects.all()})

    assert excinfo.value.context == {'template': ['all-group-names.markdown']}


def test_has_support_for_elapsed_time_in_template_render(settings):
    settings.PERFORMANCE_LIMITS = {
        'Template.render': {
            'time': {
                'total': 0
            }
        }
    }
    template = loader.get_template('all-group-names.markdown')
    with freeze_time('2016-09-29 15:52:01') as frozen_time:
        class SlowIterable(object):
            def __iter__(self):
                yield 'foo'
                frozen_time.tick(timedelta(seconds=5))
                yield 'bar'

        with pytest.raises(LimitViolationError) as excinfo:
            template.render(context={'groups': SlowIterable()})

    assert excinfo.value.context == {'template': ['all-group-names.markdown']}
