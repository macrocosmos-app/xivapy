## XIVAPI Client

The Client class is the core of this library, and thus has the most features. It takes a bit to walk through all of them, so it's best to categorize them by feature:

### Getting data from Sheets

The easiest item is fetching row(s) from sheets as mentioned in the [quickstart](../index.md#quickstart), but there's a lot of extra options for the `sheets` method, which changes the return type. In short:

* Using `row=` results in **one** (or None) Model returns
* Using `rows=` results in an async iterator which return Model(s)

Some brief examples:

#### Sheets - One Item

```python
class ContentFinderCondition(xivapy.Model):
    row_id: int
    Name: str

async with xivapy.Client() as client:
    result = await client.sheet(ContentFinderCondition, row=44)
```

#### Sheets - Multiple Items

```python
class ContentFinderCondition(xivapy.Model):
    row_id: int
    Name: str

client = xivapy.Client()
async for row in client.sheet(ContentFinderCondition, rows=[1, 2, 99, 41, 6])
```

!!! Note

    `rows` can be take any sort of Sequence type, and even iterators (async included!)

### Searching for data

If you need to search for data, you need one (or more!) models and a query. Let's start with a simple example:

```python
class ContentFinderCondition(xivapy.Model):
    row_id: int
    Name: str

client = xivapy.Client()
async for result in client.search(ContentFinderCondition, query='Name~"The"'):
    print(result)
```

This searches for every instance of content that has 'The' in the name. You'll see several `SearchResult` entries, with some extra fields:

```
SearchResult(score=0.375, sheet='ContentFinderCondition', row_id=39, data=ContentFinderCondition(row_id=39, Name='the Aery'))
SearchResult(score=0.375, sheet='ContentFinderCondition', row_id=585, data=ContentFinderCondition(row_id=585, Name='the Burn'))
SearchResult(score=0.33333334, sheet='ContentFinderCondition', row_id=34, data=ContentFinderCondition(row_id=34, Name='the Vault'))
SearchResult(score=0.33333334, sheet='ContentFinderCondition', row_id=57, data=ContentFinderCondition(row_id=57, Name='the Navel'))
```

SearchResults are the wrapper around your actual requested content, but have some useful tidbits of data:

| Field  | Type            | Description                                                                         |
| -----  | --------------- | ----------------------------------------------------------------------------------- |
| score  | `float`         | How closely this matches to your query (from 0.0 to 1.0 - higher is a better match) |
| sheet  | `str`           | What sheet this came from                                                           |
| row_id | `int`           | The row in the sheet this entry comes from                                          |
| data   | `xivapy.Model`  | The content formatted by your model                                                 |

!!! note

    You may notice that the `query` parameter is a string. You can use [QueryBuilder](./query.md) to build these query strings programmatically.

#### Searching multiple sheets for data

The above example is nice, but what if you wanted to search multiple sheets? You can do that by providing a tuple of models to search:

```python
class ContentFinderCondition(xivapy.Model):
    row_id: int
    Name: str

class ContentUICategory(xivapy.Model):
    row_id: int
    Name: str

client = xivapy.Client()
async for result in client.search((ContentFinderCondition, ContentUICategory), query='Name~"Savage"'):
    print(result.data.Name)
```

Now, if you're typing this up in an IDE with good python support, you might be noticing something here: it knows about the fields in `result.data` - this is because the return type is `AsyncIterator[SearchResult[ContentFinderCondition | ContentUICategory]]`. As long as you can narrow the scope via match/instanceof/etc for custom fields, the IDE will happily autocomplete whatever you want.

!!! warning

    You can put any number of Models that you want in the search query and it will work, but the type checking breaks down after 3 models - this is partially by design since complex queries for several sheets of data is unlikely to be useful beyond the basics of searching for a field common to all of them.

### Retrieving non-json data

Some methods of the client return `bytes` - usually things related to assets, icons, and maps. They all function roughly the same:

```python
map_jpg = await client.map('s1d1', '00')
loading_screen_png = await client.asset(path='ui/loadingimage-nowloading_base01_hr1.tex', format='png')
icon_webp = await client.icon(20650, format='webp')
```

You can write these to a file and get images right out of it. If you want more specifics, check out the associated functions.

!!! note

    The only formats supported are `jpg`, `webp`, and `png`. If you're using an IDE, it helpfully gives those options for you anyway!

### Customizing data received

Most of the constructor options for the client are based around customizing where and what kind of data is being received - look at the constructor for [`xivapy.Client`](#client). However, at a high level, you can customize the base url, api base path, and batch size (for methods like `sheet` and `search`). There are two functions that might be important for fetching *specific kinds of data*

* `game_version` - a version string (you can get a list with `client.versions()`) that specifically requests that version of the data. If you want to pin all your data to 7.2, for instance, you can absolutely do that.
* `schema_version` - not fully supported in the client yet, but this lets you pin the *shape* of the data returned by a request. See the [xivapi docs](https://v2.xivapi.com/docs/guides/pinning/#schemas) for more information

## Client API

### Client

::: xivapy.client.Client

### SearchResult

::: xivapy.client.SearchResult
