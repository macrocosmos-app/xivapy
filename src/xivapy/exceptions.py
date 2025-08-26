"""Exceptions for xivapy."""

from typing import Optional, Any

import httpx
from pydantic import ValidationError

__all__ = [
    'XIVAPIError',
    'XIVAPIHTTPError',
    'ModelValidationError',
    'QueryBuildError',
]


class XIVAPIError(Exception):
    """Base exception for all xivapy-related errors."""

    def __init__(self, message: str, details: Optional[dict[str, Any]] = None) -> None:
        """Base exception for all xivapy-related errors.

        This exception will be raised if none of the other exceptions are appropriate;
        otherwise this acts as a base class for all xivapy-related exceptions.

        Args:
            message: Standard Exception message
            details: An optional dict[str, Any] with information about the exception
        """
        super().__init__(message)
        self.details = details or {}


class XIVAPIHTTPError(XIVAPIError):
    """HTTP-related errors when communicating with XIVAPI."""

    def __init__(
        self, message: str, status_code: int, response: Optional[httpx.Response] = None
    ) -> None:
        """Raised when the upstream service raises an issue.

        Typically, the library will try to recover unless the api has provided
        data in a format we don't understand (because it was changed), or the
        server indicates an issue with an obvious status code of failure (e.g., 500)

        Args:
            message: Standard Exception message
            status_code: The return code from upstream
            response: Optional upstream httpx.Response object, if any
        """
        super().__init__(message)
        self.status_code = status_code
        self.response = response


class ModelValidationError(XIVAPIError):
    """Raised when API response data doesn't validate against the model schema."""

    def __init__(
        self,
        model_class: type,
        validation_error: ValidationError,
        raw_data: Optional[dict] = None,
    ) -> None:
        """Raised when xivapy.Model fails to validate.

        Essentially a wrapper around pydantic's ValidationError, but
        also provides the raw data that failed to validate for the
        consumer to perhaps figure out what went wrong.

        Args:
            model_class: The model that failed validation
            validation_error: A pydantic validation error explaining what failed to validate
            raw_data: The data that failed to validate
        """
        message = f'Failed to validate data for model {model_class.__name__}: {validation_error}'
        super().__init__(message)
        self.model_class = model_class
        self.validation_error = validation_error
        self.raw_data = raw_data


class QueryBuildError(XIVAPIError):
    """Raised when there's an error building a query."""

    def __init__(self, message: str, query_parts: Optional[list[str]] = None) -> None:
        """Raised when queries fail to build.

        This could be caused in validation situations (such as marking a
        query as both required and excluded), or in situations where the
        query will fail to build for some exotic reason.

        Args:
            message: Standard Exception message
            query_parts: The parts of the query that failed
        """
        super().__init__(message)
        self.query_parts = query_parts or []
