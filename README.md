# A simple tool to parse the abnormal JSON

The only function implemented in this module is `parse`.

`parse` is similar to json.loads. However, it corrects some mistakes that LLM can make.

It can be installed with `pip install sick-json` and used with `import sick_json;sick_json.parse(something)`.

### TL;DR
This module interpret
```json5
some description here..
[{
    "name": "Kim", // required
    'age': 13, /* optional */
},
{
    name: "Lee",
    age: "\14", 
]
```
to
```json
[{"name": "Kim", "age": 13}, {"name": "Lee", "age": "14"}]
```

It can also be validated/calibrated via pydantic.
```python
import sick_json
from pydantic import BaseModel

class Student(BaseModel):
    name: str
    age: int
    
sick_json.parse(r"""
some description here..
[{
    "name": "Kim", // required
    'age': 13, /* optional */
},
{
    name: "Lee",
    age: "\14", 
]
""", pydantic_model=list[Student])
```
```
[{'name': 'Kim', 'age': 13}, {'name': 'Lee', 'age': 14}]
```

### Case by Case

By default, it uses a JSON5 parser, which solves the following problems.

- Identifiers without quotes
```json5
{
    name: "Kim"
}
```
- Trailing comma
```json5
{
    "name": "Kim",
}
```
- JS-style comment
```json5
{
    "name": "Kim" // something
}
```

The JSON5x parser, a slight variation of the JSON5 parser, parses the following syntax.

- Allow "True" and "False"
```json5
{
    "name": "Kim",
    "is_good_guy": True
}
```
- Unclosed brackets
```json5
{"name": "Kim",
```
```json5
[[{"some":{"name": "Kim"], "thing"]
```
- Ignore invalid escape sequence
```json5
{"name": "Kim", "age": "\18"}
```

Additionally, it heuristically solves a few problems.

- Verbose before and after JSON
```json5
blah blah blah
{
    "name": "Kim"
}
blah blah blah
```
- If you have multiple JSONs, it will return the longest by default, or you can specify a pydantic format.
```python
import sick_json
from pydantic import BaseModel
maybe_json = 'blah{"name": "Kim"}blah{"names": ["Kim", "Lee"]}blah'
sick_json.parse(maybe_json)
# it return {"names": ["Kim", "Lee"]}
class MyModel(BaseModel):
    name: str
sick_json.parse(maybe_json, pydantic_model=MyModel)
# it return {"name": "Kim"}
```
- Type-correcting by pydantic model
```python
import sick_json
from pydantic import BaseModel
maybe_json = '{"name": "Kim", "age": "13"}'
class MyModel(BaseModel):
    name: str
    age: int
sick_json.parse(maybe_json, pydantic_model=MyModel)
# it return {"name": "Kim", "age": 13}
```
