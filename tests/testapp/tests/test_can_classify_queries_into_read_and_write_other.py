import pytest
from django_performance_testing.queries import classify_query


@pytest.mark.parametrize('sql', [
    'QUERY = u\'SELECT "auth_group"."id", "auth_group"."name" FROM "auth_group"\' - PARAMS = ()',  # noqa
    'QUERY = \'SELECT "auth_group"."id", "auth_group"."name" FROM "auth_group"\' - PARAMS = ()',  # noqa

], ids=['py2', 'py3'])
def test_can_parse_select(sql):
    assert 'read' == classify_query(sql)


@pytest.mark.parametrize('sql', [
    'QUERY = \'INSERT INTO "auth_group" ("name") VALUES (%s)\' - PARAMS = (\'foo\',)',  # noqa
    'QUERY = u\'INSERT INTO "auth_group" ("name") VALUES (%s)\' - PARAMS = (\'foo\',)',  # noqa

], ids=['py2', 'py3'])
def test_can_parse_insert(sql):
    assert 'write' == classify_query(sql)
