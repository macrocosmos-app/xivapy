"""Tests for query.py."""

from pydantic import ValidationError
from pydantic.fields import Field
import pytest

from xivapy.query import QueryBuilder, QueryDescriptor, Query
from xivapy.exceptions import QueryBuildError
from xivapy.model import QueryField, FieldMapping, Model
from xivapy.types import LangDict


@pytest.mark.unit
def test_compound_where_query():
    """Test multiple items under .where()."""
    query = QueryBuilder().where(Name='Test', Level=50)
    assert query.build() == 'Name="Test" Level=50'


@pytest.mark.unit
def test_contains_query():
    """Test contains query."""
    query = QueryBuilder().contains(Name='sword')
    assert query.build() == 'Name~"sword"'


@pytest.mark.unit
def test_comparison_operators():
    """Test both > and < operations."""
    query = QueryBuilder().gt(Level=50).lt(Level=100)
    assert query.build() == 'Level>50 Level<100'


@pytest.mark.unit
def test_required_modifier():
    """Test marking a query as required (+)."""
    query = QueryBuilder().where(Name='Test').required()
    assert query.build() == '+Name="Test"'


@pytest.mark.unit
def test_excluded_modifier():
    """Test marking a query as excluded (-)."""
    query = QueryBuilder().where(Name='Test').excluded()
    assert query.build() == '-Name="Test"'


@pytest.mark.unit
def test_empty_query():
    """Test an empty query."""
    query = QueryBuilder()
    assert query.build() == ''


@pytest.mark.unit
def test_comparison_equal_operators():
    """Test >= and <= operators."""
    query = QueryBuilder().gte(Level=50).lte(Level=60)
    assert query.build() == 'Level>=50 Level<=60'


@pytest.mark.unit
def test_or_any_with_query_builder():
    """Test query grouping using only QueryBuilder."""
    query = (
        QueryBuilder()
        .contains(Name='the')
        .or_any(
            QueryBuilder().contains(Name='extreme'),
            QueryBuilder().contains(Name='savage'),
        )
    )
    assert query.build() == 'Name~"the" (Name~"extreme" Name~"savage")'


@pytest.mark.unit
def test_bool_values_serialize_correctly():
    """Test that bool values in a query correctly serialize to their lowercase forms."""
    query = QueryBuilder().where(One=True, Two=False).build()

    assert 'One=true' in query
    assert 'Two=false' in query


@pytest.mark.unit
def test_required_exclude_on_same_query():
    """Test making a query as required and excluded."""
    with pytest.raises(QueryBuildError):
        query = (
            QueryBuilder()
            .where(Name='The Winding Spirals of Bahumhant')
            .required()
            .excluded()
        )
        query.build()


@pytest.mark.unit
def test_basic_model_querying():
    """Test SQLAlchemy-style field querying with models."""

    class Item(Model):
        name: QueryField[str] = QueryField(FieldMapping('Name'))
        Level: QueryField[int]

    # Basic equality
    # Do not examine how these expressions work under the hood.
    # There is only sadness there, and lots of pre-runtime trickery
    # to make systems like pyright and mypy happy about this
    query = QueryBuilder().where(Item.name == 'Potion')
    assert query.build() == 'Name="Potion"'

    # Contains
    query = QueryBuilder().where(Item.name.contains('Something'))
    assert query.build() == 'Name~"Something"'

    # Comparison
    query = QueryBuilder().where(Item.Level >= 50)
    assert query.build() == 'Level>=50'

    # Multiple or'd conditions
    query = QueryBuilder().where(Item.name == 'Hyper Potion').where(Item.Level < 50)
    assert query.build() == 'Name="Hyper Potion" Level<50'


@pytest.mark.unit
def test_nested_model_queries():
    """Test queries when the field is nested."""

    class Item(Model):
        name: QueryField[str] = QueryField(FieldMapping('Name'))
        nested_id: QueryField[int] = QueryField(FieldMapping('Nested.Foo.Id'))

    query = QueryBuilder().where(Item.nested_id == 4)
    assert query.build() == 'Nested.Foo.Id=4'


@pytest.mark.unit
@pytest.mark.regression
def test_optional_field_none_handling():
    """Test that optional QueryFields are set to None when missing from API data.

    Regression test for issue where missing optional fields stored QueryField instances instead of None values.
    """
    from typing import Union, Optional

    class Test(Model):
        row_id: QueryField[int]
        name: QueryField[Optional[str]] = QueryField(FieldMapping('Name'))

    result = Test.model_validate(
        {
            'row_id': 4,
        }
    )

    assert isinstance(result, Test)
    assert result.row_id == 4
    # Verify fields *are* None
    assert result.name is None
    # Verify fields are not anything they shouldn't be
    assert not isinstance(result.name, (QueryField, QueryDescriptor, str))


@pytest.mark.unit
@pytest.mark.regression
def test_union_none_handling():
    """Test that both Union[T, None] and T | None syntax work identically.

    Regression test for Union type detection with modern Python | syntax
    vs legacy Optional[] syntax.
    """
    from typing import Union

    class Test(Model):
        row_id: QueryField[int]
        name: QueryField[Union[str, None]]
        description: QueryField[str | None]

    result = Test.model_validate(
        {
            'row_id': 444,
        }
    )

    assert isinstance(result, Test)
    assert result.row_id == 444
    # Verify fields *are* None
    assert result.name is None
    assert result.description is None
    # Verify fields are not anything they shouldn't be
    assert not isinstance(result.name, (QueryField, QueryDescriptor, str))
    assert not isinstance(result.description, (QueryField, QueryDescriptor, str))


@pytest.mark.unit
@pytest.mark.regression
@pytest.mark.integration
def test_pydantic_schema_generation():
    """Test that QueryField[T] integrates properly with pydantic validation.

    Regression test for pydantic core schema generation with QueryField types.
    """
    from typing import Optional, Annotated

    class Test(Model):
        row_id: QueryField[int]
        name: QueryField[str] = QueryField(FieldMapping('Name'))
        level: Annotated[int, FieldMapping('Level')]
        Description: str
        optional_field: QueryField[Optional[int]]

    # Test mixed styles validate as expected
    result = Test.model_validate(
        {'row_id': 123, 'Name': 'Foo', 'Level': 90, 'Description': 'Some Text'}
    )

    assert isinstance(result, Test)
    assert result.row_id == 123
    assert result.name == 'Foo'
    assert result.level == 90
    assert result.Description == 'Some Text'
    assert result.optional_field is None

    # Test that fields are required
    with pytest.raises(ValidationError) as exc_info:
        Test.model_validate(
            {
                'row_id': 'definitely not an int',
                'Name': 'Bar',
                'Level': 100,
                'Description': 'Hello',
            }
        )

    errors = exc_info.value.errors()
    assert any(error['loc'] == ('row_id',) for error in errors)

    # Test missing field
    with pytest.raises(ValidationError) as exc_info:
        Test.model_validate(
            {
                'Name': 'Hello',
                'Level': 44,
                'Description': 'Once upon a time, we were missing a row id',
            }
        )

    # Fields that are marked as QueryField should still be a QueryField
    assert (
        getattr(Test.model_fields['row_id'].annotation, '__origin__', None)
        is QueryField
    )
    # Fields that are marked as plain things should be none
    assert getattr(Test.model_fields['Description'].annotation, '__origin__', -1) is -1
    # Fields that were marked with Annotated should also be none
    assert getattr(Test.model_fields['level'].annotation, '__origin__', -1) is -1


@pytest.mark.unit
@pytest.mark.regression
def test_query_descriptor_protocol_implementation():
    """Test that QueryDescriptor.__get__ works for both class and instance access.

    Regression test for descriptor protocol parameter bug and proper class vs instance access patterns.
    """

    class Test(Model):
        row_id: QueryField[int]
        Name: QueryField[str]

    # Uninstantiated model fields should be QueryDescriptor
    assert isinstance(Test.row_id, QueryDescriptor)
    # ...and should return Query objects when using some magic methods
    assert isinstance(Test.row_id == 0, Query)
    assert isinstance(Test.row_id <= 0, Query)
    assert isinstance(Test.Name.contains('foo'), Query)

    # Model instances, however, should have the field value on access
    result = Test.model_validate(
        {
            'row_id': 4,
            'Name': 'Foo',
        }
    )
    assert result.row_id == 4
    assert isinstance(result.row_id, int)


@pytest.mark.unit
@pytest.mark.regression
def test_queryfield_mapping_preservation():
    """Test that QueryField FieldMapping info is preserved through metaclass.

    Regression test for ensuring _queryfield_mappings are properly stored and accessible after metaclass transformation.
    """

    class Test(Model):
        id: QueryField[int] = QueryField(FieldMapping('row_id'))
        name: QueryField[str] = QueryField(FieldMapping('Name'))
        nested_field: QueryField[str] = QueryField(FieldMapping('Content.BGM.File'))
        lang_field: QueryField[LangDict] = QueryField(
            FieldMapping('Title', languages=['en', 'fr'])
        )

    # Verify that get_xivapi_fields() returns correct field specs
    expected_fields = {
        'row_id',
        'Name',
        'Content.BGM.File',
        'Title@lang(en)',
        'Title@lang(fr)',
    }
    assert Test.get_xivapi_fields() == expected_fields

    # Verify that mapping information is preserved
    assert hasattr(Test, '_queryfield_mappings')
    mappings = getattr(Test, '_queryfield_mappings', {})
    assert 'id' in mappings
    assert 'name' in mappings
    assert 'nested_field' in mappings
    assert 'lang_field' in mappings

    # Check FieldMapping objects are preserved
    id_mapping = mappings.get('id')
    assert isinstance(id_mapping, FieldMapping)
    assert id_mapping.base_field == 'row_id'

    lang_mapping = mappings.get('lang_field')
    assert isinstance(lang_mapping, FieldMapping)
    assert lang_mapping is not None
    assert lang_mapping.base_field == 'Title'
    assert lang_mapping.languages == ['en', 'fr']

    # Check that the fields were transitioned to QueryDescriptor objects and have the right field
    assert isinstance(Test.id, QueryDescriptor)
    assert isinstance(Test.name, QueryDescriptor)
    assert Test.id.xivapi_field == 'row_id'
    assert Test.name.xivapi_field == 'Name'
    assert Test.nested_field.xivapi_field == 'Content.BGM.File'
    assert Test.lang_field.xivapi_field == 'Title'
