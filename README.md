# xivapy

An async python client for accessing XIVAPI data for Final Fantasy XIV.

## Features

* Custom model support powered by pydantic
* Async python
* Type hints throughout for pleasant developer experience
* All major endpoints of xivapi covered

## Installation

```
pip install git+https://github.com/macrocosmos-app/xivapy.git@main
```

## Quick Start

The easiest way to use the client is to define a model and try looking through a sheet with a search.

```python
import typing
from pydantic import Field
import xivapy

class ContentFinderCondition(xivapy.Model):
    # Custom map a python field to an xivapi field name
    id: int = Field(alias='row_id')
    # compress language fields into a dictionary for easy viewing
    # for this, however, you'll need to set up a default dict for it to use
    # The output of this is:
    # {
    #   'en': "The Protector and the Destroyer",
    #   'de': "Schützer des Volkes, Schlächter des Volkes",
    #   'fr': "Protecteurs et destructeurs",
    #   'ja': "護る者、壊す者"
    # }
    # Optional languages will be omitted
    name: Annotated[xivapy.LangDict, xivapy.FieldMapping('Name', languages=['en', 'de', 'fr', 'ja'])] = Field(default_factory=lambda: xivapy.LangDict.copy())
    # get a deeply nested (and optional) field lifted up into a top-level field
    bgm_file: Annotated[str | None, xivapy.FieldMapping('Content.BGM.File')] = None
    # by default, the sheet to be searched will be the name of the model
    # if you wish to override this, set the following:
    #__sheetname__ = 'SomeOtherSheetName'

async with xivapy.Client() as client:
    # Search ContentFinderCondition for all content that mentor roulette applies to
    async for content in client.search(ContentFinderCondition, query=xivapy.QueryBuilder().where(MentorRoulette=1)):
        # Data is typed as SearchResult[ContentFinderCondition], accessable by the `.data` field
        print(f'{content.data.name} ({content.data.id}) - {content.data.bgm_file}')

    # The same thing, but for a single id:
    result = await client.sheet(ContentFinderCondition, row=998)
    if result is not None:
        # result is a ContentFinderCondition instance
        print(result)
    # You can also search for multiple ids:
    async for result in client.sheet(ContentFinderCondition, rows=[1, 3, 99, 128]):
        # result is of type ContentFinderCondition
        print(result)
```

## API Reference

This is only a basic overview of the library; as documentation is developed, this section will be removed/changed

### Core Classes

**`xivapy.Client`**:
* `search(model: xivapy.Model, query: xivapy.QueryBuilder | str)` - Search sheets with a query
* `search(models: tuple[xivapy.Model], query: xivapy.QueryBuilder | str)` - Search multiple sheets with a query
* `sheet(model: xivapy.Model, *, row: int = N)` - Pull a single row from a sheet
* `sheet(model: xivapy.Model, *, rows: list[int] = [...])` - Pull several rows from a sheet
* `asset(path: str, format: xivapy.Format = 'png')` - Retrieve an asset from the game (defaults to png format)
* `icon(icon_id: int, format: xivapy.Format = 'jpg')` - Retrieve an icon from the game
* `map(territory: str, index: str)` - Retrieve a (composed) map from the game
* `versions()` - Get available game versions
* `sheets()` - List all available sheets

**`xivapy.Model`**:
* Inherit to create a typed data class for use with client methods - they provide the field parameters and sheet name automatically
* Use fields with `xivapy.FieldMapping` to map API fields to model fields:

```python
custom_name: Annotated[str, xivapy.FieldMapping('Name')]
```

* If your model name does not match the sheet name, you can set the sheet name with `__sheetname__ = 'CorrectSheetName'`

**`xivapy.QueryBuilder`** - Build search queries
* `.where(Field=value)` - looking for exact matches; can be compounded:

```python
QueryBuilder().where(Name='Foo', Bar='Baz')
```

* `.contains(Field='text')` - Search within fields

```python
QueryBuilder().contains(Name='the') # equivalent to `Name~"the"
```

* Supports `>`, `>=`, `<`, `<=` with `.gt`, `.gte`, `.lt`, `.lte`
* `.required()` / `.excluded()` - makes the previous item as required or excluded

### Types

**`xivapy.LangDict`** - `TypedDict` representing the return fields of items like `Name@lang(en)`
**`xivapy.Format`** - Listed formats that are acceptable for `asset` method

## Development

The only real prerequisite you need is [uv](https://docs.astral.sh/uv/); afterwards:

* `git clone https://github.com/macrocosmos-app/xivapy`
* `uv sync --locked`

Afterwards, you should be able to develop against the library or use it with `uv run python` in a shell (for example) - it's an editable package inside the virtual environment.

### Code quality

To ensure code quality, install the pre-commit hooks with:

```
uv run pre-commit install --install-hooks
```

This ensures that commits follow a baseline quality and typing standard. This project uses `ruff` for formatting and checking (see [docs](https://docs.astral.sh/ruff/)); configure your formatter or use `uv run ruff format ...` as appropriate for your environment.

For typing, this project uses mypy; you can check with `uv run mypy` for a basic check, though the pre-commit hooks have a few extra flags.

### Testing and coverage

You can run the existing tests (and get coverage) with

```
uv run coverage run -m pytest
uv run coverage report
```

## License

MIT License - see LICENSE file

## Links

* https://v2.xivapi.com
* https://github.com/macrocosmos-app/xivapy/issues
