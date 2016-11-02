from datetime import timedelta
from django import template
from django.template.engine import Engine
from django_performance_testing.core import LimitViolationError
from freezegun import freeze_time
import pytest


def test_there_is_a_correct_templatetag_library():
    """
    see https://docs.djangoproject.com/en/1.10/howto/custom-template-tags/
    """
    from django_performance_testing.templatetags import djpt_limits
    assert hasattr(djpt_limits, 'register')
    assert isinstance(djpt_limits.register, template.Library)
    assert 'djptlimit' in djpt_limits.register.tags


# The below tests are based on the registry's content. Tests will rely on the
# global defaults that are tested elsewhere in the test*registry*.py files
class SlowRendering(object):
    def __init__(self, frozen_time, render_in_seconds):
        self.frozen_time = frozen_time
        self.render_in_seconds = render_in_seconds

    def __str__(self):
        self.frozen_time.tick(timedelta(seconds=self.render_in_seconds))
        return 'rendered slowly in {} seconds'.format(
            self.render_in_seconds)


@pytest.fixture
def sample_template():
    template_string = """
    {% load djpt_limits %}
    {% djptlimit 'TimeLimit' total=3 %}
    {{ slow_rendering }}
    {% enddjptlimit %}
    """
    return Engine.get_default().from_string(template_string)


def test_renders_inner_content(sample_template):
    with freeze_time('2016-11-02 10:33:00') as frozen_time:
        fast_enough = SlowRendering(
            frozen_time=frozen_time, render_in_seconds=3)
        fast_enough_context = template.context.Context(
            {'slow_rendering': fast_enough})
        assert sample_template.render(fast_enough_context).strip() == \
            'rendered slowly in 3 seconds'


def test_limits_can_be_used_as_template_tags(sample_template):
    with freeze_time('2016-11-02 10:33:00') as frozen_time:
        too_slow = SlowRendering(frozen_time=frozen_time, render_in_seconds=5)
        too_slow_context = template.context.Context(
            {'slow_rendering': too_slow})
        with pytest.raises(LimitViolationError) as excinfo:
            rendered_content = sample_template.render(too_slow_context)
            print(rendered_content)  # to get debug info
        assert excinfo.value.actual == '5.0'
        assert excinfo.value.limit == 3
