class BeforeAfterWrapper(object):
    def __init__(self, wrapped_self, method_to_wrap_name):
        self.wrapped_self = wrapped_self
        self.method_to_wrap_name = method_to_wrap_name
        self.orig_method = getattr(self.wrapped_self, self.method_to_wrap_name)
        setattr(self.wrapped_self, self.method_to_wrap_name, self.wrap)

    def wrap(self, *a, **kw):
        self.before_hook()
        try:
            return self.orig_method(*a, **kw)
        finally:
            self.after_hook()

    def before_hook(self):
        pass

    def after_hook(self):
        pass
