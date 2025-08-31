Xivapi has a query syntax that you can absolutely pass to the client's `search` method as a built string, but xivapy provides a way of programatically build queries. Let's look at some query types you can do, and how to build them with `QueryBuilder`

### Simple searches

Let's say you want to search the Item sheet where ItemUICategory is 44.

In xivapi terms, this would be:

```
ItemUICategory=44
```

To search with this string, you can absolutely do that:

```python
async for item in client.search(Item, query='ItemUICategory=44')
    print(item)
```

But you can also use the `QueryBuilder` class to do the same thing:

```python
query = QueryBuilder().where(ItemUICategory=44)
async for item in client.search(Item, query=query)
```

`where()` is the simplest way of specifying items. You can also provide strings and booleans. Let's look at a few examples:

| xivapi query                       | QueryBuilder syntax                                           |
| ---------------------------------- | ------------------------------------------------------------- |
| `Name="Spinning Edge"`             | `QueryBuilder().where(Name='Spinning Edge')`                  |
| `IsPvP=false`                      | `QueryBuilder().where(IsPvP=False)`                           |
| `Name="Spinning Edge" IsPvP=false` | `QueryBuilder().where(Name='Spinning Edge', IsPvP=False)`     |
| `ItemResult.Name="Bronze Ingot"`   | `QueryBuilder().where(**{'ItemResult.Name': 'Bronze Ingot'})` |

!!! note

    The QueryBuilder api is still very basic, hence why the last table example shows a workaround for nested field searching. A better querying system is in planning that should feel more pythonic.


There are also other methods that mimic `where`, but have different functionality. Let's find all ContentFinderCondition entries where the name *contains* 'coil':

```python
# Equivalent to Name~"coil"
query = QueryBuilder().contains(Name='coil')
async for content in client.search(ContentFinderCondition, query=query):
    print(content.data)
```

As you can guess by now, it's all key=value entries. Here's the complete list:

| QueryBuilder method              | Built output                | Description                                                                      |
| -------------------------------- | --------------------------- | -------------------------------------------------------------------------------- |
| `.gt(ClassJobLevelRequired=50)`  | `ClassJobLevelRequired>50`  | Searches for items where the value is greater than the listed number             |
| `.gte(ClassJobLevelRequired=50)` | `ClassJobLevelRequired>=50` | Searches for items where the value is greater than or equal to the listed number |
| `.lt(ClassJobLevelRequired=50)`  | `ClassJobLevelRequired<50`  | Searches for items where the value is less than the listed number                |
| `.lte(ClassJobLevelRequired=50)` | `ClassJobLevelRequired<=50` | Searches for items where the value is less than or equal to the listed number    |

### Marking queries as required or excluded

Combining some of the examples above, let's say want to search for actions that *aren't* pvp actions, so you might assume the following is correct:

```python
query = QueryBuilder().where(IsPvP=False).contains(Name=search_param)  # => 'IsPvP=false Name~"Broil"'
```

Well, let's give that a test:

```python
>>> actions = []
>>> async for result in client.search(Action, query=xivapy.QueryBuilder().contains(Name='Broil').where(IsPvP=False)):
...     actions.append(result)
...
>>> len(actions)
49201
```

That's.. a lot of actions. And if you look through them, you might notice actions where `IsPvP=true` - but what gives? This is because individual items are "OR" or "optional". Let's visualize your request as an if statement:

```python
if name in action.name or action.is_pvp == False:
```

That's not what we intended to ask for at all. In xivapy, you can mark a query as "required" with `+`:

```
+Name~"Broil" IsPvP=false
```

Which will mark that the name **must** contain "Broil". In xivapy, you can do this by using `.required()` after a query:

```python
QueryBuilder().contains(Name='Broil').required().where(IsPvP=False)
```

So let's try this:

```python
>>> async for result in client.search(Action, query=xivapy.QueryBuilder().contains(Name='Broil').required().where(IsPvP=False)):
...     actions.append(result.data)
...
>>> len(actions)
11
```

This is certainly better, but I get the feeling that this isn't quite what we want either. Let's investigate:

```python
>>> from pprint import pprint
>>> pprint(actions)
[Action(name='Broil', is_pvp=False),
 Action(name='Broil', is_pvp=False),
 Action(name='Broil II', is_pvp=False),
 Action(name='Broil II', is_pvp=False),
 Action(name='Broil II', is_pvp=False),
 Action(name='Broil IV', is_pvp=False),
 Action(name='Broil III', is_pvp=False),
 Action(name='Broil III', is_pvp=False),
 Action(name='Embroiling Flame', is_pvp=False),
 Action(name='Embroiling Flame', is_pvp=False),
 Action(name='Broil IV', is_pvp=True)]
```

Oh no, `IsPvP` is *optional* too. All we did was end up telling xivapi "The name *must* contain 'Broil' or pvp is false". Well, let's mark them both as required:

```python
>>> actions = []
>>> async for result in client.search(Action, query=xivapy.QueryBuilder().contains(Name='Broil').required().where(IsPvP=False).required()):
...     actions.append(result.data)
...
>>> pprint(actions)
[Action(name='Broil', is_pvp=False),
 Action(name='Broil', is_pvp=False),
 Action(name='Broil II', is_pvp=False),
 Action(name='Broil II', is_pvp=False),
 Action(name='Broil II', is_pvp=False),
 Action(name='Broil IV', is_pvp=False),
 Action(name='Broil III', is_pvp=False),
 Action(name='Broil III', is_pvp=False),
 Action(name='Embroiling Flame', is_pvp=False),
 Action(name='Embroiling Flame', is_pvp=False)]
```

Yes! This is what we want - well, except for the last two, but that's a technicality. There's another option like `.required()` called `excluded()`, it does what you might expect:

```python
>>> async for result in client.search(Action, query=xivapy.QueryBuilder().contains(Name='Broil').required().where(IsPvP=True).excluded()):
...     actions.append(result.data)
...
>>> pprint(actions)
[Action(name='Broil', is_pvp=False),
 Action(name='Broil', is_pvp=False),
 Action(name='Broil II', is_pvp=False),
 Action(name='Broil II', is_pvp=False),
 Action(name='Broil II', is_pvp=False),
 Action(name='Broil IV', is_pvp=False),
 Action(name='Broil III', is_pvp=False),
 Action(name='Broil III', is_pvp=False),
 Action(name='Embroiling Flame', is_pvp=False),
 Action(name='Embroiling Flame', is_pvp=False)]
```

Note that we changed `IsPvP` to *True*, but then `excluded()` it, which ends up with the same result that you're looking for here.

The lesson to learn here is that query items are "or" by default, instead of an "and" (unless you mark both terms as required) - if you're treating it like an if statement with an `and`, you must use `required()`/`excluded()` on both items to get what you want.

## Query API

### QueryBuilder

::: xivapy.query.QueryBuilder

### Query

::: xivapy.query.Query

### Group

::: xivapy.query.Group
