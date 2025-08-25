# ruff: noqa: D100, D101, D103

import pytest

from xivapy.client import Client
from xivapy.model import Model


@pytest.fixture
def client():
    return Client()


@pytest.fixture
def sample_model_data():
    # TODO: get some real data
    return {
        'row_id': 1,
        'Name': 'Test Item',
        'Level': 50,
    }


class TestModel(Model):
    __sheetname__ = 'TestSheet'
    row_id: int
    name: str = ''
    level: int = 0


@pytest.fixture
def test_model_class():
    return TestModel
