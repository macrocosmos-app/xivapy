"""xivapy, an async Python client for XIVAPI for Final Fantasy XIV."""

from xivapy.client import Client, SearchResult
from xivapy.query import Query, QueryBuilder, Group
from xivapy.model import FieldMapping, Model

# TODO: maybe scope this so people can xivapi.types.Format?
# For now the api surface is small, so we don't have conflicts anyway
from xivapy.types import LangDict, Format
import xivapy.exceptions as exceptions

__all__ = [
    'Client',
    'SearchResult',
    'Query',
    'QueryBuilder',
    'Group',
    'FieldMapping',
    'Model',
    'LangDict',
    'Format',
    'exceptions',
]
