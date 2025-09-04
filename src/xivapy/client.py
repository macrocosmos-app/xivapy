"""Classes related to xivapi client functions (fetching sheets, searching, etc)."""

from __future__ import annotations

from typing import AsyncIterable, Any, Self, Coroutine, cast, Sequence
from collections.abc import Iterable
from typing import Optional, AsyncIterator, overload
from itertools import batched
from dataclasses import dataclass
from re import match

import httpx
from aiostream.stream import chunks
from pydantic import ValidationError

from xivapy.model import Model
from xivapy.query import QueryBuilder
from xivapy.types import Format
from xivapy.exceptions import XIVAPIHTTPError, ModelValidationError
from xivapy.version import VERSION

__all__ = ['Client', 'SearchResult']


@dataclass
class SearchResult[T]:
    """Returned as part of using `xivapy.Client`'s search() method."""

    score: float
    sheet: str
    row_id: int
    data: T


class Client:
    """Async client for gathering data from xivapi rest api.

    Provides methods that touch all documented endpoints in xivapi. For information on
    those endpoints, please read https://v2.xivapi.com/api/docs.

    Args:
        base_url: Base URL for xivapi host; defaults to 'https://v2.xivapi.com'
        base_api_path: API path prevfix; defaults to '/api'
        game_version: Default game version for requests; defaults to 'latest'
        schema_version: Default schema version to use for requests
        batch_size: For the sheets endpoint, it will fetch in batches of that size

    Example:
        ```python
        class Item(xivapy.Model):
            id: Annotated[int, xivapy.FieldMapping('row_id')]
        client = xivapy.Client()
        item = await client.sheet(Item, row=123)
        print(item)
        await client.close()
        ```
    """

    def __init__(
        self,
        base_url: str = 'https://v2.xivapi.com',
        base_api_path: str = '/api',
        game_version: str = 'latest',
        schema_version: Optional[str] = None,
        batch_size: int = 100,
    ) -> None:
        """Initialize the Client with the given parameters."""
        self.base_url = base_url
        self.base_api_path = base_api_path
        transport = httpx.AsyncHTTPTransport(retries=3)
        self._client = httpx.AsyncClient(
            base_url=base_url,
            timeout=30.0,
            transport=transport,
            # TODO: let people set their own UA for this
            headers={'User-Agent': f'xivapi/{VERSION}'},
            limits=httpx.Limits(max_keepalive_connections=5, max_connections=10),
        )
        self.game_version = game_version
        self.schema_version = schema_version
        self.batch_size = batch_size

    async def close(self) -> None:
        """Close the interior HTTP client."""
        await self._client.aclose()

    # TODO: is there a better way to do this?
    def _add_version_params(self, params: dict) -> None:
        """Add version and schema parameters to request params if not already present."""
        if 'version' not in params:
            params['version'] = self.game_version
        if 'schema' not in params and self.schema_version:
            params['schema'] = self.schema_version

    def _flatten_item_data(self, data: dict) -> dict:
        """Extract and flatten row data from API response."""
        if not data or 'row_id' not in data:
            # TODO: maybe raise an exception or something?
            # Returning {} feels like losing data
            return {}

        processed_data = data.get('fields', {})
        processed_data['row_id'] = data['row_id']

        return processed_data

    async def __aenter__(self) -> Self:
        """Begin an async context where the client closes itself afterwards."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit the async context and close the session."""
        await self._client.aclose()

    def patch(self, version: str) -> None:
        """Sets the version for all endpoints to the version provided."""
        self.game_version = version

    async def versions(self) -> list[str]:
        """Retrieve a list of available game versions supported by the API."""
        try:
            response = await self._client.get(f'{self.base_api_path}/version')
            response.raise_for_status()
        except httpx.HTTPStatusError as e:
            raise XIVAPIHTTPError(
                f'Failed to get versions: {e}',
                status_code=e.response.status_code,
                response=e.response,
            )

        data = response.json()

        # flatten data
        version_names = []
        for version in data.get('versions', []):
            version_names.extend(version.get('names', []))

        return version_names

    # TODO: I wonder if index could just be a number that we 0-pad
    async def map(
        self, territory: str, index: str, version: Optional[str] = None
    ) -> Optional[bytes]:
        """Retrieve a composed map from the api.

        Args:
            territory: A 4-character string in the format of [letter][number][letter][number]
            index: A 2-digit (0-padded) numerical string
            version: A game version to fetch from

        Returns:
            A bytes object that that is a jpeg formatted map, or None
        """
        if not match(r'^[a-zA-Z]\d[a-zA-Z]\d$', territory):
            raise ValueError(
                f'Territory must be 4 characters in format [letter][digit][letter][digit], got: {territory}'
            )
        if not match(r'\d{2}$', index):
            raise ValueError(f'Index must be a 2-digit zero-padded number, got {index}')

        params = {}
        if version is not None:
            params['version'] = version
        self._add_version_params(params)

        try:
            response = await self._client.get(
                f'{self.base_api_path}/asset/map/{territory}/{index}', params=params
            )
            response.raise_for_status()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return None
            raise XIVAPIHTTPError(
                f'Failed to get map {territory}/{index}: {e}',
                status_code=e.response.status_code,
                response=e.response,
            )

        return response.content

    async def sheets(self, version: Optional[str] = None) -> list[str]:
        """Gets a list of all sheets supported by the api."""
        params = {}
        if version is not None:
            params['version'] = version
        self._add_version_params(params)
        try:
            response = await self._client.get(
                f'{self.base_api_path}/sheet', params=params
            )
            response.raise_for_status()
        except httpx.HTTPStatusError as e:
            raise XIVAPIHTTPError(
                f'Failed to get sheets: {e}',
                status_code=e.response.status_code,
                response=e.response,
            )

        data = response.json()

        # massage data
        sheets = []
        for sheet in data.get('sheets', []):
            if (name := sheet.get('name')) is not None:
                sheets.append(name)

        return sheets

    @overload
    def search[T: Model](
        self,
        model_spec: type[T],
        query: QueryBuilder | str,
        **params,
    ) -> AsyncIterator[SearchResult[T]]: ...
    @overload
    def search[T1: Model, T2: Model](
        self,
        model_spec: tuple[type[T1], type[T2]],
        query: QueryBuilder | str,
        **params,
    ) -> AsyncIterator[SearchResult[T1 | T2]]: ...
    @overload
    def search[T1: Model, T2: Model, T3: Model](
        self,
        model_spec: tuple[type[T1], type[T2], type[T3]],
        query: QueryBuilder | str,
        **params,
    ) -> AsyncIterator[SearchResult[T1 | T2 | T3]]: ...
    def search(
        self,
        model_spec: type[Model] | tuple[type[Model], ...],
        query: QueryBuilder | str,
        **params,
    ) -> Any:
        """Search XIVAPI for data using a query.

        Args:
            model_spec: Model class or tuple of model classes to search the sheets for.
            query: A QueryBuilder search or a plain string with the search terms
            **params: Additional search parameters

        Returns:
            AsyncIterator yielding SearchResult objects with data typed against your model_spec

        Example:
            ```python
            class ContentFinderCondition(Model):
                name: Annotated[str, FieldMapping('Name')]
                content_type: Annotated[str, FieldMapping('ContentType.Name')]

            async for result in client.search(ContentFinderCondition, 'ContentType.Name="Trials"'):
                print(f'{result.data.name} - {result.data.content_type}')

            query = QueryBuilder().where(ItemLevelRequired=690).contains(Name='extreme')
            async for result in client.search(ContentFinderCondition, query):
                # result.data is still properly typed
            ```
        """
        return self._search_impl(model_spec, query, **params)

    async def _search_impl(
        self,
        model_spec: type[Model] | tuple[type[Model], ...],
        query: QueryBuilder | str,
        **params,
    ) -> AsyncIterator[SearchResult[Model]]:
        """The underlying search implementation method."""
        # EVERYTHING MUST BE TUPLES
        models: tuple[type[Model], ...]
        if isinstance(model_spec, type):
            models = (model_spec,)
        else:
            models = model_spec

        sheets = {model.get_sheet_name() for model in models}

        if 'fields' not in params:
            fields = {model.get_fields_str() for model in models}
            params['fields'] = ','.join(fields)

        if isinstance(query, QueryBuilder):
            query_str = query.build()
        else:
            query_str = str(query)

        search_params = {'sheets': ','.join(sheets), 'query': query_str, **params}
        self._add_version_params(search_params)

        # Create model lookup table
        model_lut = {model.get_sheet_name(): model for model in models}

        cursor = None

        while True:
            current_params = search_params.copy()
            if cursor:
                current_params['cursor'] = cursor
                current_params.pop('query', None)

            try:
                response = await self._client.get(
                    f'{self.base_api_path}/search', params=current_params
                )
                response.raise_for_status()
            except httpx.HTTPStatusError as e:
                raise XIVAPIHTTPError(
                    f'Search failed: {e}',
                    status_code=e.response.status_code,
                    response=e.response,
                )

            data = response.json()

            for result in data.get('results', []):
                sheet_name = result.get('sheet')
                if sheet_name in model_lut:
                    model_class = model_lut[sheet_name]

                    processed_data = self._flatten_item_data(
                        {
                            'row_id': result['row_id'],
                            'fields': result.get('fields', {}),
                        }
                    )

                    try:
                        model_instance = model_class.model_validate(processed_data)
                    except ValidationError as e:
                        raise ModelValidationError(model_class, e, processed_data)
                    yield SearchResult(
                        score=result.get('score', 0.0),
                        sheet=sheet_name,
                        row_id=result['row_id'],
                        data=model_instance,
                    )
            # Are there more pages?
            cursor = data.get('next')
            if not cursor:
                break

    async def asset(
        self, path: str, format: Format = 'png', version: Optional[str] = None
    ) -> Optional[bytes]:
        """Fetches an asset from the game, formatted into a more user-friendly format.

        Args:
            path: The path to fetch from
            format: The format for the resource to be formatted as ('jpg', 'png', 'webp')
            version: A game version to fetch from

        Returns:
            A bytes object in the format requested, or None if not found.
        """
        params = {
            'path': path,
            'format': format,
        }
        if version is not None:
            params['version'] = version
        self._add_version_params(params)
        try:
            response = await self._client.get(
                f'{self.base_api_path}/asset', params=params
            )
            response.raise_for_status()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return None
            raise XIVAPIHTTPError(
                f'Failed to get asset {path}: {e}',
                status_code=e.response.status_code,
                response=e.response,
            )

        return response.content

    async def icon(
        self, icon_id: int, format: Format = 'jpg', version: Optional[str] = None
    ) -> Optional[bytes]:
        """Fetches an icon resource from the game by id.

        Args:
            icon_id: The icon id in game data.
            format: The format for the icon to be in (defaults to 'jpg')
            version: A game version to fetch from

        Returns:
            A bytes object of the icon in the selected format, or None if not found.
        """
        folder = f'{icon_id // 1000 * 1000:06d}'
        path = f'ui/icon/{folder}/{icon_id:06d}_hr1.tex'
        return await self.asset(path, format=format, version=version)

    @overload
    def sheet[T: Model](
        self,
        model_class: type[T],
        *,
        row: int,
        **params,
    ) -> Coroutine[Any, Any, Optional[T]]: ...
    @overload
    def sheet[T: Model](
        self,
        model_class: type[T],
        *,
        rows: Iterable[int] | AsyncIterable[int],
        **params,
    ) -> AsyncIterator[T]: ...
    def sheet[T: Model](
        self,
        model_class: type[T],
        *,
        row: Optional[int] = None,
        rows: Optional[Iterable[int] | AsyncIterable[int]] = None,
        **params,
    ) -> Coroutine[Any, Any, Optional[T]] | AsyncIterator[T]:
        """Fetch one or more rows from a sheet.

        Args:
            model_class: An xivapy.Model class for the results to be coerced to
            row: A single row id to fetch
            rows: Multiple row ids to fetch
            **params: Extra parameters which are passed to the sheets endpoint

        Returns:
            This returns either:
            * A single row formatted by the model given
            * An AsyncIterator of the rows requested
            * None in the case of the item not being found
        """
        if row is not None and rows is not None:
            raise ValueError("Cannot specify both 'row' and 'rows'")

        if row is not None:
            return self._get_single_row(model_class, row, **params)
        elif rows is not None:
            return self._get_multiple_rows(model_class, rows, **params)
        else:
            raise ValueError("Must specify either 'row' or 'rows'")

    async def _get_single_row[T: Model](
        self,
        model_class: type[T],
        row: int,
        **params,
    ) -> Optional[T]:
        """An internal method for fetching a single row."""
        self._add_version_params(params)
        if 'fields' not in params:
            params['fields'] = model_class.get_fields_str()

        try:
            response = await self._client.get(
                f'{self.base_api_path}/sheet/{model_class.get_sheet_name()}/{row}',
                params=params,
            )
            response.raise_for_status()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return None
            raise XIVAPIHTTPError(
                f'Failed to get sheet rows for {model_class.get_sheet_name()}: {e}',
                status_code=e.response.status_code,
                response=e.response,
            )

        data = response.json()
        if not data or 'row_id' not in data:
            return None
        processed_data = self._flatten_item_data(data)

        try:
            return model_class.model_validate(processed_data)
        except ValidationError as e:
            raise ModelValidationError(model_class, e, processed_data)

    async def _get_multiple_rows[T: Model](
        self,
        model_class: type[T],
        rows: Iterable[int] | AsyncIterable[int],
        **params,
    ) -> AsyncIterator[T]:
        """An internal method for fetching multiple rows."""
        self._add_version_params(params)
        if 'fields' not in params:
            params['fields'] = model_class.get_fields_str()

        if hasattr(rows, '__aiter__'):
            # mypy can't resolve aiostream types correctly in some cases - see upstream issue:
            # https://github.com/vxgmichel/aiostream/issues/105
            async with chunks(rows, self.batch_size).stream() as streamer:  # pyright: ignore[reportArgumentType]
                async for batch in streamer:
                    batch_seq = cast(Sequence[int], batch)
                    async for item in self._process_batch(
                        model_class, batch_seq, **params
                    ):
                        yield item
        else:
            for batch in batched(rows, self.batch_size):  # pyright: ignore[reportArgumentType]
                async for item in self._process_batch(model_class, batch, **params):
                    yield item

    async def _process_batch[T: Model](
        self, model_class: type[T], batch: Sequence[int], **params
    ) -> AsyncIterator[T]:
        # TODO: allow overriding batch-size in sheet
        rows_param = ','.join(str(id) for id in batch)

        try:
            response = await self._client.get(
                f'{self.base_api_path}/sheet/{model_class.get_sheet_name()}',
                params={**params, 'rows': rows_param},
            )
            response.raise_for_status()
        except httpx.HTTPStatusError as e:
            raise XIVAPIHTTPError(
                '', status_code=e.response.status_code, response=e.response
            )

        data = response.json()

        for item_data in data.get('rows', []):
            if not item_data or 'row_id' not in item_data:
                continue

            processed_data = self._flatten_item_data(item_data)
            try:
                yield model_class.model_validate(processed_data)
            except ValidationError as e:
                raise ModelValidationError(model_class, e, processed_data)
