# Conversion

`from_dict(type_hint, value)` accepts more than dictionaries: it converts a value
according to a target type. `to_dict(value)` produces a Python representation.

## Dataclasses and containers

```python
from __future__ import annotations

from dataclasses import dataclass
from nightjar import from_dict, to_dict


@dataclass
class Settings:
    retries: int
    labels: list[str]


settings = from_dict(Settings, {"retries": "3", "labels": ["daily"]})
assert settings.retries == 3
assert to_dict(settings) == {"retries": 3, "labels": ["daily"]}
assert from_dict(list[int], ["1", "2"]) == [1, 2]
```

Ordinary dataclasses convert declared fields recursively and ignore unknown
input keys. Missing required fields fail during construction. Lists, mappings,
and tuples recurse through Nightjar's custom conversion rules. Conversion does
not select registered implementations; use `dispatch` for that.

## Pydantic models

Use your installed Pydantic version's model definitions and validators. Nightjar
delegates model validation to that version and dumps v2 models with
`model_dump(mode="python")` or v1 models with `dict()`. Pydantic dataclasses also
use their native validation.

Scalar coercion follows Pydantic, so behavior can differ between major versions.
Ordinary, unannotated unions are tried in declared order until a conversion
succeeds. See [compatibility](../compatibility.md).

## Python output

`to_dict` is not a JSON encoder. Tuples remain tuples, and values such as dates or
UUIDs can remain Python objects. Unmatched values are deep-copied. Use a custom
converter when an application requires a particular representation.

`to_dict` includes dataclass fields or the model's serialized fields. It does
not inject discriminator values from registrations or include dataclass
`ClassVar` attributes. Declare discriminator fields explicitly when the output
must contain them.
