from __future__ import annotations

from typing import Self, Any
from dataclasses import dataclass


@dataclass
class Query:
    field: str
    operation: str
    value: Any
    required: bool = False
    excluded: bool = False

    def __str__(self) -> str:
        # TODO: complain if both are set to True
        if self.required:
            prefix = '+'
        elif self.excluded:
            prefix = '-'
        else:
            prefix = ''
        if isinstance(self.value, str) and self.operation in ['=', '~']:
            escaped_value = f'"{self.value}"'
        else:
            escaped_value = str(self.value)
        return f'{prefix}{self.field}{self.operation}{escaped_value}'


class QueryBuilder:
    def __init__(self) -> None:
        self.clauses: list[Query | Group] = []

    def where(self, **kwargs) -> Self:
        for field, value in kwargs.items():
            self.clauses.append(Query(field, '=', value))
        return self

    def contains(self, **kwargs) -> Self:
        for field, value in kwargs.items():
            self.clauses.append(Query(field, '~', value))
        return self

    def gt(self, **kwargs) -> Self:
        for field, value in kwargs.items():
            self.clauses.append(Query(field, '>', value))
        return self

    def gte(self, **kwargs) -> Self:
        for field, value in kwargs.items():
            self.clauses.append(Query(field, '>=', value))
        return self

    def lt(self, **kwargs) -> Self:
        for field, value in kwargs.items():
            self.clauses.append(Query(field, '<', value))
        return self

    def lte(self, **kwargs) -> Self:
        for field, value in kwargs.items():
            self.clauses.append(Query(field, '<=', value))
        return self

    def required(self) -> Self:
        if self.clauses:
            last = self.clauses[-1]
            if isinstance(last, Query):
                last.required = True
            elif isinstance(last, Group):
                last.required = True
        return self

    def excluded(self) -> Self:
        if self.clauses:
            last = self.clauses[-1]
            if isinstance(last, Query):
                last.excluded = True
            elif isinstance(last, Group):
                last.excluded = True
        return self

    def or_any(self, *items: Query | QueryBuilder) -> Self:
        self.clauses.append(Group(list(items)))
        return self

    def build(self) -> str:
        if not self.clauses:
            return ''
        return ' '.join(str(clause) for clause in self.clauses)

    def __str__(self) -> str:
        return self.build()


@dataclass
class Group:
    items: list[Query | QueryBuilder]
    required: bool = False
    excluded: bool = False

    def __str__(self) -> str:
        prefix = '+' if self.required else '-' if self.excluded else ''
        inner = ' '.join(str(item) for item in self.items)
        return f'{prefix}({inner})'
