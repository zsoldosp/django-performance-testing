from django.contrib.auth.models import Group
from django.template import loader
import pytest


def test_has_support_for_number_of_queries_in_templates(db, settings):
    print(settings.TEMPLATES)
    settings.PERFORMANCE_LIMITS = {
        'Template.render': {'count_limit': 0}}
    template = loader.get_template('all-group-names.markdown')
    with pytest.raises(ValueError) as excinfo:
        template.render(context={'groups': Group.objects.all()})

    expected_error_message = 'Too many (1) queries (limit: 0) ' \
        '{\'template\': [\'all-group-names.markdown\']}'
    actual_error_message = str(excinfo.value)
    assert actual_error_message.endswith(expected_error_message)
