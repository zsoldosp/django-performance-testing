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


class DelegatingProxy(object):
    """
    Proxy for accessing the wrapped object's attributes, while allowing
    overwriting specific methods
    """
    def __init__(self, wrapped):
        self.__dict__['wrapped'] = wrapped

    def __getattr__(self, item):
        return getattr(self.wrapped, item)

    def __setattr__(self, name, value):
        return setattr(self.wrapped, name, value)

    def __delattr__(self, name):
        return delattr(self.wrapped, name)

    def __eq__(self, other):
        return self.wrapped == other

    def __ne__(self, other):
        return self.wrapped != other

    def __len__(self):
        return len(self.wrapped)

    def __iter__(self):
        return iter(self.wrapped)
