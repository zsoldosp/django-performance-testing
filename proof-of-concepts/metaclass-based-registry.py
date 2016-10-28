from django.utils import six

registry = {}


class RegistryMeta(type):

    def __new__(mcs, name, bases, attrs):
        new_cls = super(RegistryMeta, mcs).__new__(mcs, name, bases, attrs)
        if mcs.is_base_cls(new_cls):
            new_cls.registry = set()
        else:
            new_cls.registry.add(new_cls)
        return new_cls

    @classmethod
    def is_base_cls(mcs, new_cls):
        fullname = '.'.join([new_cls.__module__, new_cls.__name__])
        base_names = [
            '.'.join([mcs.__module__, 'Base']),
        ]
        return fullname in base_names


class Base(six.with_metaclass(RegistryMeta)):
    pass


class A(Base):
    pass


class B(Base):
    pass


def foo():
    class C(Base):
        pass

print(Base.registry)
foo()
print(Base.registry)
