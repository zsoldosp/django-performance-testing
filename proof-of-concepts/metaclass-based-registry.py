from django.utils import six


class RegistryMeta(type):

    def __new__(mcs, name, bases, attrs):
        new_cls = super(RegistryMeta, mcs).__new__(mcs, name, bases, attrs)
        if mcs.is_base_cls(new_cls):
            new_cls.registry = {}
        else:
            name = new_cls.__name__
            # fail on duplicate names - this will make template tags neater
            if name in new_cls.registry:
                raise TypeError(
                    'Duplicate  name {} for registry {}. Try to set {},'
                    'but we already have {}'.format(
                        name, mcs, new_cls, new_cls.registry[name]
                    )
                )
            new_cls.registry[name] = new_cls
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

foo()
for name, cls in Base.registry.items():
    print([name, cls()])


class B(Base):  # noqa: F811
    pass
