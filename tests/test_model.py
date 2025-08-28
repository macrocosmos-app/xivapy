"""Tests related to xivapy models."""

from typing_extensions import Annotated
from xivapy.model import Model, FieldMapping


def test_model_sheet_name_from_class():
    """Test that we get the class name when no sheet name is defined."""

    class TestItem(Model):
        name: str

    assert TestItem.get_sheet_name() == 'TestItem'


def test_model_sheet_name_from_sheetname():
    """Test getting sheet name from defined field."""

    class CustomModel(Model):
        name: str
        __sheetname__ = 'Ackchyally'

    assert CustomModel.get_sheet_name() == 'Ackchyally'


def test_basic_model_validation():
    """Test that fields map even without specific fields defined."""

    class SimpleModel(Model):
        row_id: int
        name: str
        level: int = 0

    data = {'row_id': 1, 'name': 'Test', 'level': 50}
    model = SimpleModel.model_validate(data)

    assert model.row_id == 1
    assert model.name == 'Test'
    assert model.level == 50


def test_get_xivapi_fields_basic():
    """Test that defined basic fields in model generate as Title Cased names for xivapi."""

    class BasicModel(Model):
        row_id: int
        Name: str
        level: int

    fields = BasicModel.get_xivapi_fields()
    expected = {'row_id', 'Name', 'level'}
    assert fields == expected


def test_get_xivapi_fields_with_override():
    """Test overriding a field name to an xivapi-specific alias."""

    class BasicModel(Model):
        id: Annotated[int, FieldMapping('row_id')]
        name: str

    fields = BasicModel.get_xivapi_fields()
    expected = {'row_id', 'name'}
    assert fields == expected


def test_model_with_no_fields():
    """Test defining an empty model."""

    class EmptyModel(Model): ...

    fields = EmptyModel.get_xivapi_fields()
    assert fields == set()
