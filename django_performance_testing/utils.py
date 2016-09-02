class BeforeAfterWrapper(object):
    def __init__(self, wrapped_self, method_to_wrap_name, context_manager):
        self.wrapped_self = wrapped_self
        self.method_to_wrap_name = method_to_wrap_name
        self.orig_method = getattr(self.wrapped_self, self.method_to_wrap_name)
        self.context_manager = context_manager
        setattr(self.wrapped_self, self.method_to_wrap_name, self.wrap)

    def wrap(self, *a, **kw):
        with self.context_manager:
            return self.orig_method(*a, **kw)
