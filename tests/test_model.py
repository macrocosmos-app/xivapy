from typing_extensions import Annotated
from xivapy.model import Model, FieldMapping


def test_model_sheet_name_from_class():
    class TestItem(Model):
        name: str

    assert TestItem.get_sheet_name() == 'TestItem'


def test_model_sheet_name_from_sheetname():
    class CustomModel(Model):
        name: str
        __sheetname__ = 'Ackchyally'

    assert CustomModel.get_sheet_name() == 'Ackchyally'


def test_basic_model_validation():
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
    class BasicModel(Model):
        row_id: int
        name: str
        level: int

    fields = BasicModel.get_xivapi_fields()
    expected = {'Row_Id', 'Name', 'Level'}
    assert fields == expected


def test_get_xivapi_fields_with_override():
    class BasicModel(Model):
        id: Annotated[int, FieldMapping('row_id')]
        name: str

    fields = BasicModel.get_xivapi_fields()
    expected = {'row_id', 'Name'}
    assert fields == expected


def test_model_with_no_fields():
    # TODO: should this error?
    class EmptyModel(Model): ...

    fields = EmptyModel.get_xivapi_fields()
    assert fields == set()
