from django_performance_testing.registry import \
    UniqueNamedClassRegistry, DuplicateNamesError
import pytest
from testapp.registry_entries_one import LimitOne as L1
from testapp.registry_entries_two import LimitTwo as L2


limit_one = 'testapp.registry_entries_one.LimitOne'
limit_two = 'testapp.registry_entries_two.LimitTwo'


@pytest.mark.parametrize(
    'dotted_paths,expected_names,expected_classes', [
        ([], [], []),
        ([limit_one, limit_two], ['LimitOne', 'LimitTwo'], [L1,  L2]),
        ([limit_two, limit_one], ['LimitTwo', 'LimitOne'], [L2, L1]),
    ], ids=[
        'empty', 'one-two', 'two-one'
    ]
)
def test_registry_building_happy_path(
        dotted_paths, expected_names, expected_classes):
    registry = UniqueNamedClassRegistry(dotted_paths)
    assert list(expected_names) == list(registry.name2cls.keys())
    assert list(expected_classes) == list(registry.name2cls.values())


def test_duplicate_name_error_is_a_value_error():
    assert issubclass(DuplicateNamesError, ValueError)


@pytest.mark.parametrize(
    'dotted_paths', [
        ([limit_one, limit_one]),
        ([
            'testapp.registry_entries_one.DuplicateNamedLimit',
            'testapp.registry_entries_one.DuplicateNamedLimit']),
    ], ids=['same twice', 'different modules, same class names']
)
def test_cannot_construct_from_list_of_duplicates(dotted_paths):
    with pytest.raises(DuplicateNamesError):
        UniqueNamedClassRegistry(dotted_paths)
