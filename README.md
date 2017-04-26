# compare
Small python utility for performing comparison between objects. It was written for purpose of testing some REST API and comparing parsed json representation of a model with its equivalent from a database.

Why don't we just use custom `json.JSONDecoder`? The thing is, when we need for example to perform comparison on two objects having iso8601 dates with different precision, You just need to implement it by ourselves.

## Features
Not many so far. For now we can compare:
- `dict`
- `list` (with respect of elements order or without)
- objects (can call conversion between types implicitly, e.g. 1 == "1")
- `datetime` (also represented as string in `iso8601`)
- user defined types - implementing of custom hooks is simple

## Use case
I encountered problem with comparison of object from deserialization of JSON from REST API with another object gathered from database with ORM library. The problem were datetimes.

Consider two objects:
```python
orm_obj = {'id': 66, 'name': 'Some long name 1', 'address_id': None, 'created': datetime.datetime(2017, 4, 26, 23, 5, 20, 409060, tzinfo=psycopg2.tz.FixedOffsetTimezone(offset=120, name=None))}

api_obj = {'name': 'Some long name 1', 'id': 66, 'address_id': None, 'created': '2017-04-26T21:05:20.409Z'}
```
Their `created` fields are different. One is `datetime` type and the other one is `str`. If we have to test many API endpoints with resources like this (and with nested ones) it's better to involve some smart utility than altering all of this data by hand.

With this utility we can do it like:
```python
import compare

# gather orm_obj and api_obj
# ...

try:
    compare.compare(orm_obj,api_obj,hooks=compare.ISO8601())
    print("Objects are equal.")
except compare.CompareError as e:
    print("Objects are different: "+str(e))
```

## Similar packages
You may also want to look at [DeepDiff](https://github.com/seperman/deepdiff), which is far more complete solution in case of comparing objects. However (as far as I know) it does not implement concept like hooks, so it is hard to add comparing with tolerance of custom types.
