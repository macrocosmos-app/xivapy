Models are the core of how data is fetched and formatted within xivapy. In general, model creation determines how robust the data is you recieve from a `sheet` or `search` call within the client.

### Creating a basic model

The most basic model is one that fetches all parameters by their given name in the dictionary. It's important that the annotated type (str, bool, etc) are correct, or the model will fail to validate.

```python
class ContentFinderCondition(xivapy.Model):
    row_id: int
    Name: str
    ContentMemberType: dict
```

Let's use it to get data on T5:

```python
>>> async with xivapy.Client() as client:
...     await client.sheet(ContentFinderCondition, row=97)
ContentFinderCondition(row_id=97, Name='the Binding Coil of Bahamut - Turn 5', ContentMemberType={'value': 3, 'sheet': 'ContentMemberType', 'row_id': 3, 'fields': {'HealersPerParty': 2, 'MeleesPerParty': 2, 'RangedPerParty': 2, 'TanksPerParty': 2, 'Unknown0': 0, 'Unknown1': 0, 'Unknown10': False, 'Unknown11': True, 'Unknown12': False, 'Unknown13': False, 'Unknown14': True, 'Unknown15': 0, 'Unknown16': 1, 'Unknown2': 8, 'Unknown3': 8, 'Unknown4': 8, 'Unknown5': 1, 'Unknown6': 0, 'Unknown7': False, 'Unknown8': False, 'Unknown9': False}})
```

This will likely suit the needs for most people to fetch in this way; you only really need the more advanced features below to customize how this data is fetched.

!!! note

    If you have multiple models that represent the same sheet (let's say you're searching for data with one Model, but fetching data from the sheet with a more comprehensive Model, you can use `__sheetname__` to override the name):

    ```python
    class JustTheName(xivapy.Model):
      __sheetname__ = 'ContentFinderCondition'
      Name: str

    class NameAndLevel(xivapy.Model):
      __sheetname__ = 'ContentFinderCondition'
      Name: str
      ClassJobLevelRequired: int
    ```

!!! warning

    `row_id` is the only special case out of all the fields you can request - the rest of the data is technically part of a `fields` parameter in the return json, but `row_id` is not part of those params; as a convenience, the `row_id` field is moved 'downwards' into the params so the model can have access to this.

### Extra field mapping parameters

The first thing you might notice is that fields like `Name` and `ClassJobLevelRequired` don't quite fit the python scheme. In these cases when you want to rename the fields themselves to be more pythonic, you can use `xivapy.FieldMapping` to map the API field to the python field:

```python
from typing import Annotated
class ContentFinderCondition(xivapy.Model):
    name: Annotated[str, xivapy.FieldMapping('Name')]
    content_member_type: Annotated[dict, xivapy.FieldMapping('ContentMemberType')]
```

This effectively works the same as the first example, but the fields have more pythonic names.

But what if we actually cared about the party composition for this content and don't want to parse the dictionary? You can use the `FieldMapping` class to customize that data too if you know the field:

```python
class ContentFinderCondition(xivapy.Model):
    id: Annotated[int, xivapy.FieldMapping('row_id')]
    name: Annotated[str, xivapy.FieldMapping('Name')]
    tanks_required: Annotated[int, xivapy.FieldMapping('ContentMemberType.TanksPerParty')]
    healers_required: Annotated[int, xivapy.FieldMapping('ContentMemberType.HealersPerParty')]
    melees_required: Annotated[int, xivapy.FieldMapping('ContentMemberType.MeleesPerParty')]
    ranged_required: Annotated[int, xivapy.FieldMapping('ContentMemberType.RangedPerParty')]
```

Now the same request returns the data that you asked for:

```
ContentFinderCondition(id=97, name='the Binding Coil of Bahamut - Turn 5', tanks_required=2, healers_required=2, melees_required=2, ranged_required=2)
```

By using `Field.Subfield` as part of your mapping, the field mapping will 'lift' the data up from the subfield, eliminating the need for the nested dictionary looking and gives you the data that you're actually asking for.

#### Getting extra languages

You can also use `xivapy.FieldMapping` to get languages (for fields that support it). Back to our example, let's say we want to know all the (supported) languages for the name(s) of T5:

```python
class ContentFinderCondition(xivapy.Model):
    # modified from the previous model
    name: Annotated[xivapy.LangDict, xivapy.FieldMapping('Name', languages=['en', 'fr', 'de', 'ja'])]
    # everything else is the same
```

And now, the model has I18n data:

```
ContentFinderCondition(name={'en': 'the Binding Coil of Bahamut - Turn 5', 'de': 'Verschlungene Schatten 5', 'ja': '大迷宮バハムート：邂逅編5'}, tanks_required=2, healers_required=2, melees_required=2, ranged_required=2)
```

!!! note

    You'll need to change the type from `str` to `xivapy.LangDict` to get this particular data output. The result is a dictionary with all the languages you request as keys of the dictionary

## Model API

### Model

::: xivapy.model.Model

### FieldMapping

::: xivapy.model.FieldMapping
