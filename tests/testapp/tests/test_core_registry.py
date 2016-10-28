from collections import OrderedDict as odict
from django_performance_testing.registry import UniqueNamedClassRegistry
import pytest


@pytest.mark.parametrize(
    'dotted_paths,expected_registry', [
        ([], odict()),
    ]
)
def test_registry_building(dotted_paths, expected_registry):
    registry = UniqueNamedClassRegistry(dotted_paths)
    assert expected_registry == registry.name2cls
