import pytest
from django_performance_testing.queries import classify_query


@pytest.mark.parametrize('sql', [
    'QUERY = u\'SELECT "auth_group"."id", "auth_group"."name" FROM "auth_group"\' - PARAMS = ()',  # noqa
    'QUERY = \'SELECT "auth_group"."id", "auth_group"."name" FROM "auth_group"\' - PARAMS = ()',  # noqa
], ids=['py2', 'py3'])
def test_can_classify_select(sql):
    assert 'read' == classify_query(sql)


@pytest.mark.parametrize('sql', [
    'QUERY = \'INSERT INTO "auth_group" ("name") VALUES (%s)\' - PARAMS = (\'foo\',)',  # noqa
    'QUERY = u\'INSERT INTO "auth_group" ("name") VALUES (%s)\' - PARAMS = (\'foo\',)',  # noqa
], ids=['py2', 'py3'])
def test_can_classify_insert(sql):
    assert 'write' == classify_query(sql)


@pytest.mark.parametrize('sql', [
    'QUERY = \'UPDATE "auth_group" SET "name" = %s\' - PARAMS = (\'bar\',)',  # noqa
    'QUERY = u\'UPDATE "auth_group" SET "name" = %s\' - PARAMS = (\'bar\',)',  # noqa
], ids=['py2', 'py3'])
def test_can_classify_update(sql):
    assert 'write' == classify_query(sql)


@pytest.mark.parametrize('sql', [
    'QUERY = \'DELETE FROM "auth_group" WHERE "auth_group"."id" IN (%s)\' - PARAMS = (1,)',  # noqa
    'QUERY = u\'DELETE FROM "auth_group" WHERE "auth_group"."id" IN (%s)\' - PARAMS = (1,)',  # noqa

], ids=['py2', 'py3'])
def test_can_classify_delete(sql):
    assert 'write' == classify_query(sql)


def test_can_classify_even_if_it_doesnt_have_the_query_prefix():
    sql = 'SELECT "auth_group"."id", "auth_group"."name" FROM "auth_group"'
    assert 'read' == classify_query(sql)


def test_can_classify_even_if_it_has_quotes_inside():
    sql = 'SELECT \'auth_group\'.\'id\', "auth_group"."name" FROM "auth_group"'
    assert 'read' == classify_query(sql)
