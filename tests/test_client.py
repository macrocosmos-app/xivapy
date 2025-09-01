"""Tests related to xivapy.Client."""

from typing import Annotated
from pytest_httpx import HTTPXMock
import httpx
import pytest

from xivapy.client import Client, SearchResult
from xivapy.model import Model
from xivapy.exceptions import ModelValidationError, XIVAPIHTTPError

from tests.fixtures.api_responses import (
    BASIC_SEARCH_RESPONSE,
    MULTI_MODEL_SEARCH_RESPONSE,
    MULTI_MODEL_SEARCH_RESPONSE_BROKEN,
    SEARCH_RESPONSE_PAGE_1,
    SEARCH_RESPONSE_PAGE_2,
    SHEET_ROWS_RESPONSE,
    VERSIONS_RESPONSE,
    SHEETS_RESPONSE,
    SHEET_ROW_RESPONSE,
)
from xivapy.model import FieldMapping
from xivapy.query import QueryBuilder


async def test_client_close():
    """Test that the client closes without exception."""
    client = Client()
    # No exception is essentially good
    await client.close()


def test_setting_patch():
    """Test setting patch as part of the client."""
    client = Client()
    client.patch('7.21')
    assert client.game_version == '7.21'


def test_flatten_item_data():
    """Test flattening api response data."""
    client = Client()
    data = {'row_id': 123, 'fields': {'Name': 'Foo'}}
    result = client._flatten_item_data(data)
    assert result == {'Name': 'Foo', 'row_id': 123}


async def test_versions_success(httpx_mock: HTTPXMock):
    """Test version endpoint with good response."""
    httpx_mock.add_response(
        url='https://v2.xivapi.com/api/version',
        json=VERSIONS_RESPONSE,
    )

    async with Client() as client:
        versions = await client.versions()
        assert '7.3x1' in versions
        assert 'latest' in versions


async def test_versions_http_error(httpx_mock: HTTPXMock):
    """Test version endpoint with bad response."""
    httpx_mock.add_response(
        url='https://v2.xivapi.com/api/version',
        status_code=500,
    )

    async with Client() as client:
        with pytest.raises(XIVAPIHTTPError) as exc_info:
            await client.versions()
        assert exc_info.value.status_code == 500


async def test_sheets_success(httpx_mock: HTTPXMock):
    """Test sheets endpoint with good response."""
    httpx_mock.add_response(
        url='https://v2.xivapi.com/api/sheet?version=latest',
        json=SHEETS_RESPONSE,
    )

    async with Client() as client:
        sheets = await client.sheets()
        assert 'Item' in sheets
        assert 'ContentFinderCondition' in sheets
        assert 'Quest' in sheets


async def test_sheets_http_error(httpx_mock: HTTPXMock):
    """Test sheets endpoint with bad response."""
    httpx_mock.add_response(
        url='https://v2.xivapi.com/api/sheet?version=latest',
        status_code=500,
    )

    async with Client() as client:
        with pytest.raises(XIVAPIHTTPError) as exc_info:
            await client.sheets()
        assert exc_info.value.status_code == 500


async def test_map_success(httpx_mock: HTTPXMock):
    """Test map endpoint with valid territory and index format."""
    httpx_mock.add_response(
        url='https://v2.xivapi.com/api/asset/map/a1b2/00?version=latest',
        content=b'abadlydrawnmapwithcrayonthatsnotevenajpg',
    )

    async with Client() as client:
        looking_for_a_good_map = await client.map('a1b2', '00')
        assert looking_for_a_good_map == b'abadlydrawnmapwithcrayonthatsnotevenajpg'


async def test_map_invalid_territory():
    """Test map with invalid territory format."""
    async with Client() as client:
        with pytest.raises(ValueError, match='Territory must be 4 characters'):
            await client.map('invalid', '00')


async def test_map_invalid_index():
    """Test map with invalid index."""
    async with Client() as client:
        with pytest.raises(
            ValueError, match='Index must be a 2-digit zero-padded number'
        ):
            await client.map('a1b2', 'invalid')


async def test_asset_success(httpx_mock: HTTPXMock):
    """Test asset with good response."""
    httpx_mock.add_response(
        url='https://v2.xivapi.com/api/asset?path=ui/icon/ultima.tex&format=png&version=latest',
        content=b'asparklerthathealstheenemy',
    )

    async with Client() as client:
        final_spell_icon = await client.asset(path='ui/icon/ultima.tex', format='png')
        assert final_spell_icon == b'asparklerthathealstheenemy'


async def test_asset_http_error(httpx_mock: HTTPXMock):
    """Test asset endpoint with bad response."""
    httpx_mock.add_response(
        url='https://v2.xivapi.com/api/asset?path=ui/icon/solution.tex&format=png&version=latest',
        status_code=500,
    )

    async with Client() as client:
        with pytest.raises(XIVAPIHTTPError, match='Failed to get asset') as exc_info:
            await client.asset(path='ui/icon/solution.tex', format='png')
        assert exc_info.value.status_code == 500


async def test_asset_none_found(httpx_mock: HTTPXMock):
    """Test asset endpoint where it isn't found."""
    httpx_mock.add_response(
        url='https://v2.xivapi.com/api/asset?path=ui/icon/selene.tex&format=png&version=latest',
        status_code=404,
    )

    async with Client() as client:
        asset = await client.asset(path='ui/icon/selene.tex', format='png')
        assert asset == None


async def test_search_success(httpx_mock: HTTPXMock):
    """Test searching something where it's a single result."""

    class TestSheet(Model):
        id: Annotated[int, FieldMapping('row_id')]
        name: Annotated[str, FieldMapping('Name')]
        level: Annotated[int, FieldMapping('Level')]

    expected_fields = TestSheet.get_fields_str()
    httpx_mock.add_response(
        url=httpx.URL(
            'https://v2.xivapi.com/api/search',
            params={
                'sheets': 'TestSheet',
                'query': '+Name="Test Item" +Level=50',
                'fields': expected_fields,
                'version': 'latest',
            },
        ),
        json=BASIC_SEARCH_RESPONSE,
    )

    client = Client()

    res_iter = aiter(client.search(TestSheet, query='+Name="Test Item" +Level=50'))

    item = await anext(res_iter)
    assert isinstance(item, SearchResult)
    assert item.score == pytest.approx(1.0)
    assert item.sheet == 'TestSheet'
    assert isinstance(item.data, TestSheet)
    assert item.data.id == 1
    assert item.data.name == 'Test Item'
    assert item.data.level == 50


async def test_paginated_search_success(httpx_mock: HTTPXMock):
    """Test getting multiple pages from the search endpoint with a cursor."""

    class TestSheet(Model):
        id: Annotated[int, FieldMapping('row_id')]
        name: Annotated[str, FieldMapping('Name')]
        level: Annotated[int, FieldMapping('Level')]

    expected_fields = TestSheet.get_fields_str()

    httpx_mock.add_response(
        url=httpx.URL(
            'https://v2.xivapi.com/api/search',
            params={
                'sheets': 'TestSheet',
                'query': 'Name~"Test Item" Level=50',
                'fields': expected_fields,
                'version': 'latest',
            },
        ),
        json=SEARCH_RESPONSE_PAGE_1,
    )
    httpx_mock.add_response(
        url=httpx.URL(
            'https://v2.xivapi.com/api/search',
            params={
                'sheets': 'TestSheet',
                'cursor': '28433b5b-7860-4395-88df-17c75c173a7c',
                'fields': expected_fields,
                'version': 'latest',
            },
        ),
        json=SEARCH_RESPONSE_PAGE_2,
    )

    client = Client()

    req_iter = aiter(client.search(TestSheet, query='Name~"Test Item" Level=50'))

    item = await anext(req_iter)
    assert isinstance(item, SearchResult)
    assert item.data.name == 'Test Item'
    assert item.data.level == 89

    item = await anext(req_iter)
    assert isinstance(item, SearchResult)
    assert item.data.name == 'Another Test Item'
    assert item.data.level == 50

    with pytest.raises(StopAsyncIteration):
        await anext(req_iter)


async def test_sheet_single_row(httpx_mock: HTTPXMock):
    """Test querying a single sheet row."""

    class Test(Model):
        id: Annotated[int, FieldMapping('row_id')]
        name: Annotated[str, FieldMapping('Name')]
        level: Annotated[int, FieldMapping('Level')]

    expected_fields = Test.get_fields_str()
    httpx_mock.add_response(
        url=httpx.URL(
            'https://v2.xivapi.com/api/sheet/Test/1',
            params={'fields': expected_fields, 'version': 'latest'},
        ),
        json=SHEET_ROW_RESPONSE,
    )

    async with Client() as client:
        result = await client.sheet(Test, row=1)

    assert result is not None
    assert isinstance(result, Test)
    assert result.id == 1
    assert result.name == 'Test Item'
    assert result.level == 50


async def test_sheet_row_not_found(httpx_mock: HTTPXMock):
    """Test a 404/None response from an endpoint."""

    class Test(Model):
        id: Annotated[int, FieldMapping('row_id')]
        name: Annotated[str, FieldMapping('Name')]
        level: Annotated[int, FieldMapping('Level')]

    expected_fields = Test.get_fields_str()
    # Test 404 handling in sheet method
    httpx_mock.add_response(
        url=httpx.URL(
            'https://v2.xivapi.com/api/sheet/Test/1234',
            params={
                'fields': expected_fields,
                'version': 'latest',
            },
        ),
        status_code=404,
    )

    async with Client() as client:
        result = await client.sheet(Test, row=1234)

    assert result is None


async def test_sheet_multiple_rows(httpx_mock: HTTPXMock):
    """Test multiple sheet responses from rows."""

    class Test(Model):
        id: Annotated[int, FieldMapping('row_id')]
        name: Annotated[str, FieldMapping('Name')]
        level: Annotated[int, FieldMapping('Level')]

    expected_fields = Test.get_fields_str()
    httpx_mock.add_response(
        url=httpx.URL(
            'https://v2.xivapi.com/api/sheet/Test',
            params={
                'rows': '1,2,3',
                'fields': expected_fields,
                'version': 'latest',
            },
        ),
        json=SHEET_ROWS_RESPONSE,
    )

    client = Client()

    result_iter = aiter(client.sheet(Test, rows=[1, 2, 3]))

    # First item
    result = await anext(result_iter)
    assert result is not None
    assert isinstance(result, Test)
    assert result.id == 1
    assert result.name == 'Test Item'
    assert result.level == 50
    # Second item
    result = await anext(result_iter)
    assert result is not None
    assert isinstance(result, Test)
    assert result.id == 2
    assert result.name == 'Second Item'
    assert result.level == 44
    # Last item
    result = await anext(result_iter)
    assert result is not None
    assert isinstance(result, Test)
    assert result.id == 3
    assert result.name == 'Final Item'
    assert result.level == 999

    with pytest.raises(StopAsyncIteration):
        await anext(result_iter)


async def test_search_with_querybuilder(httpx_mock: HTTPXMock):
    """Test using search with QueryBuilder instead of plain strings."""

    class TestSheet(Model):
        row_id: int

    query = QueryBuilder().where(Name='Test Item').required()

    httpx_mock.add_response(
        url=httpx.URL(
            'https://v2.xivapi.com/api/search',
            params={
                'sheets': TestSheet.get_sheet_name(),
                'query': query.build(),
                'fields': TestSheet.get_fields_str(),
                'version': 'latest',
            },
        ),
        json=BASIC_SEARCH_RESPONSE,
    )

    client = Client()
    search_iter = aiter(client.search(TestSheet, query=query))

    result = await anext(search_iter)
    assert result is not None
    assert isinstance(result, SearchResult)
    item = result.data
    assert isinstance(item, TestSheet)
    assert item.row_id == 1

    with pytest.raises(StopAsyncIteration):
        await anext(search_iter)


async def test_search_multiple_models(httpx_mock: HTTPXMock):
    """Test a search result which has multiple Models in the response."""

    class TestSheet(Model):
        id: Annotated[int, FieldMapping('row_id')]
        name: Annotated[str, FieldMapping('Name')]
        level: Annotated[int, FieldMapping('Level')]

    class OtherSheet(Model):
        id: Annotated[int, FieldMapping('row_id')]
        name: Annotated[str, FieldMapping('Name')]
        field_id: Annotated[int, FieldMapping('Field', raw=True)]

    to_search = (TestSheet, OtherSheet)

    expected_sheets = ','.join({m.get_sheet_name() for m in to_search})
    expected_fields = ','.join({m.get_fields_str() for m in to_search})

    httpx_mock.add_response(
        url=httpx.URL(
            'https://v2.xivapi.com/api/search',
            params={
                'sheets': expected_sheets,
                'fields': expected_fields,
                'query': 'Name~"Item"',
                'version': 'latest',
            },
        ),
        json=MULTI_MODEL_SEARCH_RESPONSE,
    )

    client = Client()

    search_iter = aiter(client.search(to_search, query='Name~"Item"'))

    item_result = await anext(search_iter)
    assert isinstance(item_result, SearchResult)
    item = item_result.data
    assert isinstance(item, Model)
    assert isinstance(item, TestSheet)
    assert item.id == 1
    assert item.name == 'Test Item'
    assert item.level == 50
    assert not hasattr(item, 'field_id')

    item_result = await anext(search_iter)
    assert isinstance(item_result, SearchResult)
    item = item_result.data
    assert isinstance(item, Model)
    assert isinstance(item, OtherSheet)
    assert item.id == 7
    assert item.name == 'Other Item'
    assert item.field_id == 14
    assert not hasattr(item, 'level')

    with pytest.raises(StopAsyncIteration):
        await anext(search_iter)


async def test_model_validation_error(httpx_mock: HTTPXMock):
    """Test raising an exception when the client gets incorrect data."""

    class Test(Model):
        row_id: int
        name: str
        level: int

    expected_fields = Test.get_fields_str()

    httpx_mock.add_response(
        url=httpx.URL(
            'https://v2.xivapi.com/api/sheet/Test/1',
            params={
                'fields': expected_fields,
                'version': 'latest',
            },
        ),
        json=SHEET_ROW_RESPONSE,
    )

    client = Client()
    with pytest.raises(ModelValidationError):
        await client.sheet(Test, row=1)


async def test_model_validation_multi_model(httpx_mock: HTTPXMock):
    """Test that model validations during mixed model searches raise exceptions and continue if caught."""

    class TestSheet(Model):
        row_id: int
        Name: str
        Level: int

    class OtherSheet(Model):
        row_id: int
        Name: str
        Description: str

    sheets = (TestSheet, OtherSheet)
    expected_sheets = ','.join({m.get_sheet_name() for m in sheets})
    expected_fields = ','.join({m.get_fields_str() for m in sheets})
    query = 'Name~"Item"'

    httpx_mock.add_response(
        url=httpx.URL(
            'https://v2.xivapi.com/api/search',
            params={
                'sheets': expected_sheets,
                'query': query,
                'fields': expected_fields,
                'version': 'latest',
            },
        ),
        json=MULTI_MODEL_SEARCH_RESPONSE_BROKEN,
    )

    client = Client()
    search_iter = client.search(sheets, query=query)

    result = await anext(search_iter)
    assert isinstance(result, SearchResult)
    data = result.data
    assert isinstance(data, TestSheet)
    assert data.row_id == 1
    assert data.Name == 'Test Item'
    assert data.Level == 50

    # should have marked that description as `str | None`
    with pytest.raises(ModelValidationError):
        await anext(search_iter)


def test_flatten_data_empty():
    """Test that flattening data bails correctly if the input is basically empty."""
    client = Client()
    result = client._flatten_item_data({})
    assert result == {}


async def test_sheet_batch_http_error(httpx_mock: HTTPXMock):
    """Test that the client raises an exception on a 500 error during sheet batching."""

    class TestModel(Model): ...

    httpx_mock.add_response(status_code=500)
    client = Client()
    with pytest.raises(XIVAPIHTTPError) as exc_info:
        async for _ in client.sheet(TestModel, rows=[1, 2, 3]):
            pass
    assert exc_info.value.status_code == 500
