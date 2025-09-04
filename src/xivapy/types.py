"""Types used in xivapy."""

from typing import Literal, TypedDict

__all__ = ['Format', 'LangDict', 'QueryOperators']

Format = Literal['png', 'jpg', 'webp']
QueryOperators = Literal['=', '~', '<', '<=', '>', '>=']


class LangDict(TypedDict, total=False):
    """A dictionary representing the different languages supported by xivapi."""

    en: str
    de: str
    fr: str
    ja: str
