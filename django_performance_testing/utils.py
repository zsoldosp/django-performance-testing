from functools import wraps


class run_with(object):
    def __init__(self, ctx_manager):
        self.ctx_manager = ctx_manager

    def __call__(self, test_fn):
        @wraps(test_fn)
        def with_ctx_mngr_wrapper(*a, **kw):
            with self.ctx_manager:
                return test_fn(*a, **kw)
        return with_ctx_mngr_wrapper


class BeforeAfterWrapper(object):
    def __init__(self, wrapped_self, method_to_wrap_name, context_manager):
        method_to_wrap = getattr(wrapped_self, method_to_wrap_name)
        setattr(
            wrapped_self, method_to_wrap_name,
            run_with(context_manager)(method_to_wrap)
        )


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
