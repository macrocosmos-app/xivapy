"""Types used in xivapy."""

from typing import Literal, TypedDict

__all__ = ['Format', 'LangDict']

Format = Literal['png', 'jpg', 'webp']


class LangDict(TypedDict, total=False):
    """A dictionary representing the different languages supported by xivapi."""

    en: str
    de: str
    fr: str
    ja: str
