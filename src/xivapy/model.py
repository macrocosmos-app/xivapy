"""xivapy Model-related classes."""

from typing import Optional, Any
from dataclasses import dataclass

from pydantic import BaseModel, model_validator

__all__ = [
    'Model',
    'FieldMapping',
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


class Model(BaseModel):
    """Base model for all xivapy queries."""

    __sheetname__: Optional[str] = None

    model_config = {'populate_by_name': True}

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
        if hasattr(field_info, 'metadata') and field_info.metadata:
            for metadata in field_info.metadata:
                if isinstance(metadata, FieldMapping):
                    return metadata
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
                    lang_dict[lang] = data.pop(field_key)
            if lang_dict:
                data[model_field] = lang_dict

        elif mapping.raw:
            field_key = f'{mapping.base_field}@as(raw)'
            if field_key in data:
                data[model_field] = data.pop(field_key)

        elif mapping.html:
            field_key = f'{mapping.base_field}@as(html)'
            if field_key in data:
                data[model_field] = data.pop(field_key)

        elif mapping.custom_spec:
            if mapping.custom_spec in data:
                data[model_field] = data.pop(mapping.custom_spec)

        else:
            # Handle nested fields
            if '.' in mapping.base_field:
                value = cls._extract_nested_field(data, mapping.base_field)
                if value is not None:
                    data[model_field] = value
            elif mapping.base_field in data:
                data[model_field] = data.pop(mapping.base_field)

        return data

    @classmethod
    def _extract_nested_field(cls, data: dict, field_path: str) -> Any:
        """Extract nested field data from xivapi response using dot notation (e.g., 'ContentType.Name')."""
        parts = field_path.split('.')
        current = data

        for i, part in enumerate(parts):
            if part in current:
                obj = current.pop(part) if i == 0 else current[part]

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

        for field_name, field_info in cls.model_fields.items():
            mapping = cls._get_field_mapping(field_info)
            if mapping:
                data = cls._process_mapped_field(data, field_name, mapping)

        return data
