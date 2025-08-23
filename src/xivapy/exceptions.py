from typing import Optional, Any

import httpx
from pydantic import ValidationError

__all__ = [
    'XIVAPIError',
    'XIVAPIHTTPError',
    'XIVAPINotFoundError',
    'ModelValidationError',
    'QueryBuildError',
]


class XIVAPIError(Exception):
    """Base exception for all xivapy-related errors."""

    def __init__(self, message: str, details: Optional[dict[str, Any]] = None) -> None:
        super().__init__(message)
        self.details = details or {}


class XIVAPIHTTPError(XIVAPIError):
    """HTTP-related errors when communicating with XIVAPI."""

    def __init__(
        self, message: str, status_code: int, response: Optional[httpx.Response] = None
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.response = response


class XIVAPINotFoundError(XIVAPIHTTPError):
    """Raised when an api request results in a not found error."""

    def __init__(self, resource: str, identifier: Optional[str] = None) -> None:
        message = f'Resource not found: {resource}'
        if identifier:
            message += f' (identifier: {identifier})'
        super().__init__(message, 404)
        self.resource = resource
        self.identifier = identifier


class ModelValidationError(XIVAPIError):
    """Raised when API response data doesn't validate against the model schema."""

    def __init__(
        self,
        model_class: type,
        validation_error: ValidationError,
        raw_data: Optional[dict] = None,
    ) -> None:
        message = f'Failed to validate data for model {model_class.__name__}: {validation_error}'
        super().__init__(message)
        self.model_class = model_class
        self.validation_error = validation_error
        self.raw_data = raw_data


class QueryBuildError(XIVAPIError):
    """Raised when there's an error building a query."""

    def __init__(self, message: str, query_parts: Optional[list[str]] = None) -> None:
        super().__init__(message)
        self.query_parts = query_parts or []
