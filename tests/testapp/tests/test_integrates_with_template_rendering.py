from django.contrib.auth.models import Group
from django.template import loader
from django_performance_testing.core import LimitViolationError
import pytest


def test_has_support_for_number_of_queries_in_templates(db, settings):
    print(settings.TEMPLATES)
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

    expected_error_message = '{\'template\': [\'all-group-names.markdown\']}'
    assert expected_error_message in str(excinfo.value)
