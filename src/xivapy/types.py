from typing import Literal, TypedDict

__all__ = ['Format', 'LangDict']

Format = Literal['png', 'jpg', 'webp']


class LangDict(TypedDict, total=False):
    en: str
    de: str
    fr: str
    ja: str
