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

# Custom mapping to a dictionary language support
class I18nDict(typing.TypedDict, total=False):
    en: str
    de: str
    fr: str
    ja: str

class ContentFinderCondition(xivapy.Model):
    # Custom map a python field to an xivapi field name
    id: int = Field(alias='row_id')
    # compress language fields into a dictionary for easy viewing
    # for this, however, you'll need to set up a default dict for it to use
    name: Annotated[I18nDict, xivapy.FieldMapping('Name', languages=['en', 'de', 'fr', 'ja'])] = Field(default_factory=lambda: I18nDict.copy())
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

## Development

## License

MIT License - see LICENSE file

## Links

* https://v2.xivapi.com
* https://github.com/macrocosmos-app/xivapy/issues
