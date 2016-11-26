import django
from django import template
from django.utils.inspect import getargspec
from django_performance_testing import core
if django.VERSION[:2] == (1, 8):
    from django.template.base import TagHelperNode, parse_bits
else:
    from django.template.library import TagHelperNode, parse_bits

register = template.Library()


def get_args_kwargs(parser, token):
    """ copied from
        django.template.(base|library).Library.simple_tag.compile_func """
    def to_limit(limit_name, **limit_kwargs):
        pass
    params, varargs, varkw, defaults = getargspec(to_limit)
    function_name = 'djptlimit'
    bits = token.split_contents()[1:]
    takes_context = False
    args, kwargs = parse_bits(
        parser, bits, params,
        varargs, varkw, defaults, takes_context, function_name)
    return args, kwargs


limit_tag_name = 'djptlimit'


@register.tag(name=limit_tag_name)
def djpt_limit(parser, token):
    [limit_name], limit_kwargs = get_args_kwargs(parser, token)
    # based on
    # https://docs.djangoproject.com/en/1.10/howto/custom-template-tags/
    nodelist = parser.parse(('end{}'.format(limit_tag_name),))
    parser.delete_first_token()
    return DjptLimitNode(nodelist, limit_name, **limit_kwargs)


class DjptLimitNode(TagHelperNode):
    def __init__(self, nodelist, limit_name, **limit_kwargs):
        extra_kwargs = {}
        if django.VERSION[:2] > (1, 8):
            extra_kwargs['func'] = None
        super(DjptLimitNode, self).__init__(
            takes_context=False, args=[limit_name], kwargs=limit_kwargs,
            **extra_kwargs
        )
        self.nodelist = nodelist

    def render(self, context):
        resolved_args, resolved_kwargs = self.get_resolved_arguments(context)
        limit = self.get_limit(*resolved_args, **resolved_kwargs)
        with limit:
            return self.nodelist.render(context)

    def get_limit(self, name, **limit_kwargs):
        limit_cls = core.limits_registry.name2cls[name]
        return limit_cls(**limit_kwargs)
