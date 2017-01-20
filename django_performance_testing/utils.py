import sys
from functools import wraps


class multi_context_manager(object):

    def __init__(self, managers, debug=False):
        if not managers:
            raise ValueError('Expected at least one manager, got 0 as arg')
        self.head_manager = managers[0]
        self.tail_managers = managers[1:]
        if self.tail_managers:
            self.next_ = multi_context_manager(self.tail_managers)
        else:
            self.next_ = None
        self.debug = debug

    def _print(self, action):
        if self.debug:
            id_ = getattr(self.head_manager, 'id_', None)
            print('{} {} {}'.format(action, type(self.head_manager), id_))

    def __enter__(self):
        self._print('entering....')
        self.head_manager.__enter__()
        if self.next_:
            try:
                self.next_.__enter__()
            except:
                self._print('exiting...')
                self.head_manager.__exit__(*sys.exc_info())
                self._print('... exited')
                raise
        self._print('... entered')

    def __exit__(self, exc_type, exc_val, exc_tb):
        try:
            if self.next_:
                self.next_.__exit__(exc_type, exc_val, exc_tb)
        finally:
            self._print('exiting...')
            self.head_manager.__exit__(exc_type, exc_val, exc_tb)
            self._print('... exited')


def with_context_manager(ctx_manager):
    def decorator(fn):
        @wraps(fn)
        def context_manager_wrapper(*a, **kw):
            with ctx_manager:
                return fn(*a, **kw)
        context_manager_wrapper.djpt_patched = True
        return context_manager_wrapper

    return decorator


def wrap_cls_method_in_ctx_manager(cls, method_name, ctx_manager,
                                   is_cls_method):
    target_method = getattr(cls, method_name)
    has_been_patched_flag = 'djpt_patched'
    if hasattr(target_method, has_been_patched_flag):
        return
    if is_cls_method:
        # as classmethod must be outermost decorator
        target_method = target_method.__func__
    wrapped_method = with_context_manager(ctx_manager)(target_method)
    if is_cls_method:
        # as classmethod must be outermost decorator
        wrapped_method = classmethod(wrapped_method)
    setattr(cls, method_name, wrapped_method)
    target_method = getattr(cls, method_name)
    assert hasattr(target_method, has_been_patched_flag), (cls, target_method)


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
