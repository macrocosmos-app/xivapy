"""Query building utilities for xivapi search."""

from __future__ import annotations

from typing import Self, Any
from dataclasses import dataclass

from xivapy.exceptions import QueryBuildError
from xivapy.types import QueryOperators

__all__ = [
    'Query',
    'QueryBuilder',
    'QueryDescriptor',
    'Group',
]


@dataclass
class Query:
    """Represents a composable query unit in xivapi's query interface.

    Provides an abstracted interface for dealing with xivapi-style
    query elements, which are created automatically as part of QueryBuilder's
    methods.

    Example:
        >>> query = (QueryBuilder()
        ...    .custom('Name', '=', 'Alexander', required=True)
        ...    .custom('ItemLevel', '>=', 50)
        ...    .required())
        >>> print(query.build())
        +Name="Alexander" +ItemLevel>=50
    """

    field: str
    operation: QueryOperators
    # TODO: scope this to number | str | bool as those are the only
    # listed ones in the docs
    value: Any
    required: bool = False
    excluded: bool = False

    def __str__(self) -> str:
        """Returns a string representation of the query."""
        if self.required and self.excluded:
            raise QueryBuildError('Query cannot be set to both required and excluded')
        if self.required:
            prefix = '+'
        elif self.excluded:
            prefix = '-'
        else:
            prefix = ''
        if isinstance(self.value, str) and self.operation in ['=', '~']:
            escaped_value = f'"{self.value}"'
        elif isinstance(self.value, bool):
            escaped_value = 'true' if self.value else 'false'
        else:
            escaped_value = str(self.value)
        return f'{prefix}{self.field}{self.operation}{escaped_value}'


class QueryDescriptor:
    """Initializes a QueryDescriptor, which QueryFields turn into at runtime."""

    def __init__(self, field_name: str, xivapi_field: str):
        """Initializes a QueryDescriptor."""
        self.field_name = field_name
        self.xivapi_field = xivapi_field

    def __get__(self, instance, owner):
        """Returns this class if not instantiated, but returns the instantiated value otherwise."""
        if instance is not None:
            return instance.__dict__.get(self.field_name)
        return self

    def __eq__(self, value: object, /) -> Query:  # type: ignore[override]
        """Returns a Query showing the field name is equal to the value."""
        return Query(self.xivapi_field, '=', value)

    def __lt__(self, value: object, /) -> Query:
        """Returns a Query showing the field name is less than the value."""
        return Query(self.xivapi_field, '<', value)

    def __le__(self, value: object, /) -> Query:
        """Returns a Query showing the field name is less than or equal to the value."""
        return Query(self.xivapi_field, '<=', value)

    def __gt__(self, value: object, /) -> Query:
        """Returns a Query showing the field name is greater than the value."""
        return Query(self.xivapi_field, '>', value)

    def __ge__(self, value: object, /) -> Query:
        """Returns a Query showing the field name is greater than or equal to the value."""
        return Query(self.xivapi_field, '>=', value)

    def contains(self, value: object, /) -> Query:
        """Returns a Query showing that the string from the value is inside the field."""
        return Query(self.xivapi_field, '~', value)


class QueryBuilder:
    """Builder for constructing xivapi search queries.

    Provides an abstracted interface for dealing with xivapi-style
    search queries, including grouping, operators like >=, ~, =, etc.
    Queries can be chained and grouped to create more complex queries.

    Example:
        >>> query = (QueryBuilder()
        ...    .contains(Name='Alexander')
        ...    .gte(ItemLevel=50)
        ...    .required())
        >>> print(query.build())
        Name="Alexander" +ItemLevel>=50
    """

    def __init__(self) -> None:
        """Initializes an empty query builder."""
        self.clauses: list[Query | Group] = []

    def where(self, *queries: Query, **kwargs) -> Self:
        """Add an equality condition to the query.

        Args:
            *queries: A list of plain queries to add to the list.
            **kwargs: Field-value pairs for exact matches.

        Returns:
            Self for method chaining.
        """
        for query in queries:
            self.clauses.append(query)
        for field, value in kwargs.items():
            self.clauses.append(Query(field, '=', value))
        return self

    def contains(self, **kwargs) -> Self:
        """Add a partial string match to the query.

        Args:
            **kwargs: Field-value pairs for partial matching.

        Returns:
            Self for method chaining.
        """
        for field, value in kwargs.items():
            self.clauses.append(Query(field, '~', value))
        return self

    def gt(self, **kwargs) -> Self:
        """Add a greater than (>) numeric comparison to the query.

        Args:
            **kwargs: Field-value pairs for comparison.

        Returns:
            Self for method chaining.
        """
        for field, value in kwargs.items():
            self.clauses.append(Query(field, '>', value))
        return self

    def gte(self, **kwargs) -> Self:
        """Add a greater than or equal (>=) numeric comparison to the query.

        Args:
            **kwargs: Field-value pairs for comparison.

        Returns:
            Self for method chaining.
        """
        for field, value in kwargs.items():
            self.clauses.append(Query(field, '>=', value))
        return self

    def lt(self, **kwargs) -> Self:
        """Add a less than (<) numeric comparison to the query.

        Args:
            **kwargs: Field-value pairs for comparison.

        Returns:
            Self for method chaining.
        """
        for field, value in kwargs.items():
            self.clauses.append(Query(field, '<', value))
        return self

    def lte(self, **kwargs) -> Self:
        """Add a less than or equal (<=) numeric comparison to the query.

        Args:
            **kwargs: Field-value pairs for comparison.

        Returns:
            Self for method chaining.
        """
        for field, value in kwargs.items():
            self.clauses.append(Query(field, '<=', value))
        return self

    def required(self) -> Self:
        """Marks the previous query item as required.

        Returns:
            Self for method chaining.
        """
        if self.clauses:
            last = self.clauses[-1]
            if isinstance(last, Query):
                last.required = True
            elif isinstance(last, Group):
                last.required = True
        return self

    def excluded(self) -> Self:
        """Marks the previous query item as excluded.

        Returns:
            Self for method chaining.
        """
        if self.clauses:
            last = self.clauses[-1]
            if isinstance(last, Query):
                last.excluded = True
            elif isinstance(last, Group):
                last.excluded = True
        return self

    def custom(self, *items: Query) -> Self:
        """Allows injecting regular Queries into QueryBuilder.

        Args:
            items: one or more Query items to be added to the list of clauses to evaluate.

        Returns:
            Self for method chaining.
        """
        self.clauses.extend(items)
        return self

    def or_any(self, *items: Query | QueryBuilder) -> Self:
        """Creates a group to match agains.

        Args:
            items: one or more Query or QueryBuilder instances to add to the group.

        Returns:
            Self for method chaining.
        """
        self.clauses.append(Group(list(items)))
        return self

    def build(self) -> str:
        """Builds the current query as a string.

        Returns:
            A string representation of the query.
        """
        if not self.clauses:
            return ''
        return ' '.join(str(clause) for clause in self.clauses)

    def __str__(self) -> str:
        """Shows the current query as a string representation.

        Returns:
            A string representation of the query.
        """
        return self.build()


@dataclass
class Group:
    """Constructs groups to be used with QueryBuilder.

    Provides an abstracted interfaces around xivapi-style nested
    grouped query items.

    Example:
        >>> query = (QueryBuilder()
        ...    .or_any( # This creates a Group instance
        ...        QueryBuilder().where(Name="The Binding Coils of Bahamut"),
        ...        Query('ClassJob.Abbreviation', '=', 'PCT'))
        ...    .required())
        >>> print(query.build())
        +(Name="The Binding Coils of Bahamud" ClassJob.Abbreviation="PCT")
    """

    items: list[Query | QueryBuilder]
    required: bool = False
    excluded: bool = False

    def __str__(self) -> str:
        """Returns a string representation of the grouping."""
        if self.required and self.excluded:
            raise QueryBuildError('Query cannot be set to both required and excluded')
        if self.required:
            prefix = '+'
        elif self.excluded:
            prefix = '-'
        else:
            prefix = ''
        inner = ' '.join(str(item) for item in self.items)
        return f'{prefix}({inner})'
