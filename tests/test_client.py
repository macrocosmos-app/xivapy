from pytest_httpx import HTTPXMock
import pytest

from xivapy.client import Client
from xivapy.exceptions import XIVAPIHTTPError


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
