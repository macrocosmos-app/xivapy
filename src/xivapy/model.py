"""xivapy Model-related classes."""

from typing import Optional, Any, get_args, Union, get_origin
import types
from dataclasses import dataclass

from pydantic import BaseModel, model_validator
from pydantic_core import core_schema

from xivapy.query import QueryDescriptor, Query


__all__ = [
    'Model',
    'FieldMapping',
    'QueryField',
]


@dataclass
class FieldMapping:
    """Map a single model field to multiple XIVAPI fields."""

    base_field: str
    languages: Optional[list[str]] = None
    raw: bool = False
    html: bool = False
    custom_spec: Optional[str] = None

    def to_field_specs(self) -> list[str]:
        """Transforms a Model field into an xivapi-understood field."""
        if self.custom_spec:
            return [self.custom_spec]

        specs = []
        if self.languages:
            for lang in self.languages:
                specs.append(f'{self.base_field}@lang({lang})')
        elif self.raw:
            specs.append(f'{self.base_field}@as(raw)')
        elif self.html:
            specs.append(f'{self.base_field}@as(html)')
        else:
            specs.append(self.base_field)

        return specs


class QueryField[T]:
    """Types a xivapy.Model field as both a field for xivapi and allows you to query with it."""

    def __init__(self, mapping: Optional[FieldMapping] = None):
        """Initializes an empty QueryField."""
        self.mapping = mapping
        self.field_name = None

    def __set_name__(self, owner, name):
        """Grabs the name of the variable and updates the owner's mappings."""
        self.field_name = name

        # Store QueryField mapping info for the metaclass to use later
        if not hasattr(owner, '_queryfield_mappings'):
            owner._queryfield_mappings = {}
        owner._queryfield_mappings[name] = self.mapping

    # These become "real" at runtime
    def __eq__(self, value: object, /) -> Query:  # type: ignore[override,empty-body]
        """Dummy method that gets replaced by QueryDescriptor at runtime."""
        ...

    def __lt__(self, value: object, /) -> Query:  # type: ignore[empty-body]
        """Dummy method that gets replaced by QueryDescriptor at runtime."""
        ...

    def __le__(self, value: object, /) -> Query:  # type: ignore[empty-body]
        """Dummy method that gets replaced by QueryDescriptor at runtime."""
        ...

    def __gt__(self, value: object, /) -> Query:  # type: ignore[empty-body]
        """Dummy method that gets replaced by QueryDescriptor at runtime."""
        ...

    def __ge__(self, value: object, /) -> Query:  # type: ignore[empty-body]
        """Dummy method that gets replaced by QueryDescriptor at runtime."""
        ...

    def contains(self, value: object, /) -> Query:  # type: ignore[empty-body]
        """Dummy method that gets replaced by QueryDescriptor at runtime."""
        ...

    @classmethod
    def __get_pydantic_core_schema__(
        cls, source_type: Any, handler: Any
    ) -> core_schema.CoreSchema:
        """Inform pydantic of the types (or None if in the union)."""
        # Get T
        type_args = get_args(source_type)
        inner_type = type_args[0] if type_args else Any

        origin = get_origin(inner_type)
        args = get_args(inner_type)
        is_optional = (origin is Union or type(inner_type) is types.UnionType) and type(
            None
        ) in args

        inner_schema = handler.generate_schema(inner_type)

        if is_optional:
            # Set the default to None instead of being itself
            inner_schema = core_schema.with_default_schema(inner_schema, default=None)

        return inner_schema


class Model(BaseModel):
    """Base model for all xivapy queries."""

    __sheetname__: Optional[str] = None
    model_config = {'populate_by_name': True}

    @classmethod
    def __pydantic_init_subclass__(cls, **kwargs):
        """Pydantic's hooked __init_subclass__; used to add QueryDescriptors to QueryField fields."""
        super().__pydantic_init_subclass__(**kwargs)

        # Now add our QueryDescriptors after Pydantic is done
        if hasattr(cls, '__annotations__'):
            for field_name, field_type in cls.__annotations__.items():
                if (
                    hasattr(field_type, '__origin__')
                    and field_type.__origin__ is QueryField
                ):
                    # Only add if we don't already have one
                    if not isinstance(getattr(cls, field_name, None), QueryDescriptor):
                        mapping = None
                        queryfield_mappings = getattr(cls, '_queryfield_mappings', {})
                        if field_name in queryfield_mappings:
                            mapping = queryfield_mappings[field_name]
                        xivapi_field = mapping.base_field if mapping else field_name
                        setattr(
                            cls, field_name, QueryDescriptor(field_name, xivapi_field)
                        )

    @classmethod
    def get_sheet_name(cls) -> str:
        """Returns the sheet name, defaulting to the class name if __sheetname__ not set."""
        if cls.__sheetname__:
            return cls.__sheetname__
        return cls.__name__

    @classmethod
    def get_fields_str(cls) -> str:
        """Returns all model fields as a comma-separated string list for XIVAPI queries."""
        return ','.join(cls.get_xivapi_fields())

    @classmethod
    def _get_field_mapping(cls, field_info) -> Optional[FieldMapping]:
        """Gets the xivapy-specific metadata for a field, if one is defined."""
        # Check metadata first (Annotated fields)
        if hasattr(field_info, 'metadata') and field_info.metadata:
            for metadata in field_info.metadata:
                if isinstance(metadata, FieldMapping):
                    return metadata

        # Check default value (looking for Queryfield)
        if hasattr(field_info, 'default') and isinstance(
            field_info.default, QueryField
        ):
            return field_info.default.mapping

        return None

    @classmethod
    def get_xivapi_fields(cls) -> set[str]:
        """Get a set of all defined field names."""
        fields = set()

        for field_name, field_info in cls.model_fields.items():
            default_field = field_info.alias or field_name
            mapping = cls._get_field_mapping(field_info)

            if mapping:
                for spec in mapping.to_field_specs():
                    fields.add(spec)
            else:
                fields.add(default_field)

        return fields

    @classmethod
    def _process_mapped_field(
        cls, data: dict[str, Any], model_field: str, mapping: FieldMapping
    ) -> dict[str, Any]:
        if mapping.languages:
            # Collect lang variants
            lang_dict = {}
            for lang in mapping.languages:
                field_key = f'{mapping.base_field}@lang({lang})'
                if field_key in data:
                    lang_dict[lang] = data[field_key]
            if lang_dict:
                data[model_field] = lang_dict

        elif mapping.raw:
            field_key = f'{mapping.base_field}@as(raw)'
            if field_key in data:
                data[model_field] = data[field_key]

        elif mapping.html:
            field_key = f'{mapping.base_field}@as(html)'
            if field_key in data:
                data[model_field] = data[field_key]

        elif mapping.custom_spec:
            if mapping.custom_spec in data:
                data[model_field] = data[mapping.custom_spec]

        else:
            # Handle nested fields
            if '.' in mapping.base_field:
                value = cls._extract_nested_field(data, mapping.base_field)
                if value is not None:
                    data[model_field] = value
            elif mapping.base_field in data:
                data[model_field] = data[mapping.base_field]

        return data

    @classmethod
    def _extract_nested_field(cls, data: dict, field_path: str) -> Any:
        """Extract nested field data from xivapi response using dot notation (e.g., 'ContentType.Name')."""
        parts = field_path.split('.')
        current = data

        for i, part in enumerate(parts):
            if part in current:
                obj = current[part]

                # Navigate through the dark fields
                if isinstance(obj, dict):
                    if 'fields' in obj and len(parts) > i + 1:
                        current = obj['fields']
                    elif i == len(parts) - 1:
                        # we've gone to the bottom of the fields
                        return obj
                    else:
                        current = obj
                else:
                    return obj if i == len(parts) - 1 else None
            else:
                return None
        return current

    @model_validator(mode='before')
    @classmethod
    def process_xivapi_response(cls, data: dict[str, Any]) -> dict[str, Any]:
        """Model validator that processes xivapi-specific response data for pydantic validation."""
        if not isinstance(data, dict):
            return data

        # Normal field mapping process
        for field_name, field_info in cls.model_fields.items():
            mapping = cls._get_field_mapping(field_info)
            if mapping:
                data = cls._process_mapped_field(data, field_name, mapping)

        # Handle optional fields - set them to None
        for field_name, field_info in cls.model_fields.items():
            if hasattr(field_info, 'default') and isinstance(
                field_info.default, QueryField
            ):
                if field_name not in data:
                    # Is the field optional?
                    annotation = cls.__annotations__.get(field_name, Any)
                    type_args = get_args(annotation)
                    if type_args:
                        inner_type = type_args[0]
                        origin = get_origin(inner_type)
                        args = get_args(inner_type)
                        is_optional = (
                            origin is Union or type(inner_type) is types.UnionType
                        ) and type(None) in args
                        if is_optional:
                            data[field_name] = None

        return data
