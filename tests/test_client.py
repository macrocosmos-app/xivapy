"""Tests related to xivapy.Client."""

from pytest_httpx import HTTPXMock
import pytest

from xivapy.client import Client
from xivapy.exceptions import XIVAPIHTTPError, XIVAPINotFoundError


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
        json={'versions': [{'names': ['latest']}, {'names': ['7.3x1']}]},
    )

    async with Client() as client:
        versions = await client.versions()
        assert 'latest' in versions
        assert '7.3x1' in versions


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
        json={'sheets': [{'name': 'Item'}, {'name': 'ContentUICondition'}]},
    )

    async with Client() as client:
        sheets = await client.sheets()
        assert 'Item' in sheets
        assert 'ContentUICondition' in sheets


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
