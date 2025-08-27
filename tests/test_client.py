"""Tests related to xivapy.Client."""

from typing import Annotated
from pytest_httpx import HTTPXMock
import httpx
import pytest

from xivapy.client import Client, SearchResult
from xivapy.model import Model
from xivapy.exceptions import XIVAPIHTTPError

from tests.fixtures.api_responses import (
    BASIC_SEARCH_RESPONSE,
    SEARCH_RESPONSE_PAGE_1,
    SEARCH_RESPONSE_PAGE_2,
    VERSIONS_RESPONSE,
    SHEETS_RESPONSE,
    SHEET_ROW_RESPONSE,
)
from xivapy.model import FieldMapping


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


# @pytest.mark.httpx_mock(assert_all_responses_were_requested=False)
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
