# xivapy - a python client for xivapi

## Installation

Install using pip with:

```
$ pip install git+https://github.com/macrocosmos-app/xivapy.git@main
```

## Quickstart

Let's fetch some data from xivapi about Phoenix Downs. To do that, we need to know some information:

* The sheet name
* The item "id"
* (Optionally) Some of the data about the item

Since we're cheating a bit, I can tell you the sheet name is `Item` and the item id is `4570`.
xivapy is designed to fetch data into validated python models, and be easy to use as part of a development
library, but that also means we need to do a little bit of front work. Let's make a model that represents the
data we want first. Let's just assume we want the name only for right now.

Start an interactive session with `python -m asyncio`, then:

```python
>>> import xivapy
>>> class Item(xivapi.Model)
...     Name: str
...
>>>
```

Then we can make a client and fetch that data:

```python
>>> async with xivapy.Client() as client:
...     await client.sheet(Item, row=4570)
...
```

This returns a pydantic model:

```
Item(Name='Phoenix Down')
```

Which is great - for a start; most people probably want more data, like how long it takes to cast and data about the icon. Let's do that now:

```python
>>> class Item(xivapy.Model):
...     Name: str
...     CastTimeSeconds: int
...     Icon: dict
...
>>> async with xivapy.Client() as client:
...     await client.sheet(Item, row=4570)
...
Item(Name='Phoenix Down', CastTimeSeconds=8, Icon={'id': 20650, 'path': 'ui/icon/020000/020650.tex', 'path_hr1': 'ui/icon/020000/020650_hr1.tex'})
```

This is (hopefully) straightforward - ask for a field, specify a type, and the model takes care of the rest! However, this is a *python* library, and we should choose more appropriate names for our fields so we can be pythonic. xivapy allows you to map fields to alternative names and more, so let's explore that briefly:

```python
>>> from xivapy import FieldMapping
>>> from typing import Annotated
>>> class Item(xivapy.Model):
...     name: Annotated[str, FieldMapping('Name')]
...     cast_time: Annotated[int, FieldMapping('CastTimeSeconds')]
...     icon: Annotated[str, FieldMapping('Icon.path_hr1')]
...
>>> async with xivapy.Client() as client:
...     await client.sheet(Item, row=4570)
...
Item(name='Phoenix Down', cast_time=8, icon='ui/icon/020000/020650_hr1.tex')
```

The *variable names* are more pythonic, but did you notice what we did with the icon variable? That's right, you can map subfields with the `.` operator and lift them right up to a top-level variable!

Finally, what if you want to know about a *bunch* of items? Well, we have to think about one thing first - not all items have a cast time, but they probably have a name and icon, so let's modify our Item for the last time:

```python
>>> class Item(xivapy.Model):
...     name: Annotated[str, xivapy.FieldMapping('Name')]
...     cast_time: Annotated[int | None, xivapy.FieldMapping('CastTimeSeconds')] = None
...     icon: Annotated[str, xivapy.FieldMapping('Icon.path_hr1')]
```

We made the optional field... well, optional - and set it to `None` as a safety. Afterwards, we just use `rows=` instead of the singular `row=` and we get multiple items!

```python
>>> async with xivapy.Client() as client:
...     async for item in client.sheet(Item, rows=[4570, 22, 18]):
...         print(item)
...
name='Phoenix Down' cast_time=8 icon='ui/icon/020000/020650_hr1.tex'
name='Flame Seal' cast_time=2 icon='ui/icon/065000/065006_hr1.tex'
name='Lightning Cluster' cast_time=2 icon='ui/icon/020000/020017_hr1.tex'
```

There's even more you can do with the library, like search sheets, build queries, and customize models further - just keep reading if you're interested.
