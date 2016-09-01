from django_performance_testing import context


class override_current_context(object):
    def __enter__(self):
        self.orig_current_context = context.current
        context.current = context.Context()
        return context.current

    def __exit__(self, exc_type, exc_val, exc_tb):
        context.current = self.orig_current_context
