from typing import Optional, Any, overload
from dataclasses import dataclass
from pydantic import BaseModel
from xivapy.query import QueryDescriptor, Query

@dataclass
class FieldMapping:
    base_field: str
    languages: Optional[list[str]] = None
    raw: bool = False
    html: bool = False
    custom_spec: Optional[str] = None
    def to_field_specs(self) -> list[str]: ...

# For type checkers, QueryField[T] looks like QueryDescriptor
class QueryField[T](QueryDescriptor):
    def __init__(self, mapping: Optional[FieldMapping] = None) -> None: ...
    def __set_name__(self, owner: Any, name: str) -> None: ...
    @classmethod
    def __get_pydantic_core_schema__(cls, source_type: Any, handler: Any) -> Any: ...

    # Descriptor stuff
    @overload
    def __get__(self, instance: None, owner: Any) -> QueryDescriptor: ...
    @overload
    def __get__(self, instance: object, owner: Any) -> T: ...

class Model(BaseModel):
    __sheetname__: Optional[str]
    @classmethod
    def get_queryfield_mappings(cls) -> dict[str, QueryDescriptor]: ...
    @classmethod
    def get_sheet_name(cls) -> str: ...
    @classmethod
    def get_fields_str(cls) -> str: ...
    @classmethod
    def get_xivapi_fields(cls) -> set[str]: ...
    @classmethod
    def process_xivapi_response(cls, data: dict[str, Any]) -> dict[str, Any]: ...
