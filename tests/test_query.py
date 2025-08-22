import pytest

from xivapy.query import QueryBuilder
from xivapy.exceptions import QueryBuildError


def test_compound_where_query():
    query = QueryBuilder().where(Name='Test', Level=50)
    assert query.build() == 'Name="Test" Level=50'


def test_contains_query():
    query = QueryBuilder().contains(Name='sword')
    assert query.build() == 'Name~"sword"'


def test_comparison_operators():
    query = QueryBuilder().gt(Level=50).lt(Level=100)
    assert query.build() == 'Level>50 Level<100'


def test_required_modifier():
    query = QueryBuilder().where(Name='Test').required()
    assert query.build() == '+Name="Test"'


def test_excluded_modifier():
    query = QueryBuilder().where(Name='Test').excluded()
    assert query.build() == '-Name="Test"'


def test_empty_query():
    query = QueryBuilder()
    assert query.build() == ''


def test_comparison_equal_operators():
    query = QueryBuilder().gte(Level=50).lte(Level=60)
    assert query.build() == 'Level>=50 Level<=60'


def test_or_any_with_query_builder():
    query = (
        QueryBuilder()
        .contains(Name='the')
        .or_any(
            QueryBuilder().contains(Name='extreme'),
            QueryBuilder().contains(Name='savage'),
        )
    )
    assert query.build() == 'Name~"the" (Name~"extreme" Name~"savage")'


def test_required_exclude_on_same_query():
    with pytest.raises(QueryBuildError):
        query = (
            QueryBuilder()
            .where(Name='The Winding Spirals of Bahumhant')
            .required()
            .excluded()
        )
        query.build()
