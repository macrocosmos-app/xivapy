# xivapy

An async python client for accessing XIVAPI data for Final Fantasy XIV.

## Features

* Custom model support powered by pydantic
* Async python
* Type hints throughout for pleasant developer experience
* All major endpoints of xivapi covered

## Installation

```
pip install xivapy
```

## Quick Start

The easiest way to use the client is to define a model and try looking through a sheet with a search.

```python
import xivapy

class ContentFinderCondition(xivapy.Model):
    # Custom map a python field to an xivapi field name
    id: xivapy.QueryField[int] = xivapy.QueryField(FieldMapping('row_id'))
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
    name: xivapy.QueryField[xivapy.LangDict] = xivapy.QueryField(FieldMapping('Name', languages=['en', 'de', 'fr', 'ja']))
    # get a deeply nested (and optional) field lifted up into a top-level field
    bgm_file: xivapy.QueryField[str | None] = xivapy.QueryField(xivapy.FieldMapping('Content.BGM.File'))
    # by default, the sheet to be searched will be the name of the model
    # if you wish to override this, set the following:
    #__sheetname__ = 'SomeOtherSheetName'

async with xivapy.Client() as client:
    # Search ContentFinderCondition for all content that mentor roulette applies to
    async for content in client.search(ContentFinderCondition, query=xivapy.QueryBuilder().where(MentorRoulette=1)):
        # Data is typed as SearchResult[ContentFinderCondition], accessable by the `.data` field
        print(f'{content.data.name.get('en', 'No English Name')} ({content.data.id}) - {content.data.bgm_file}')

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

You can see the docs at https://macrocosmos-app.github.io/xivapy

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
