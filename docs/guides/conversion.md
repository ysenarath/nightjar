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

Ordinary dataclasses convert declared fields recursively and reject undeclared
input keys with `TypeError`. Missing required fields fail during construction.
Lists, mappings, and tuples recurse through Nightjar's custom conversion rules. Conversion does
not select registered implementations; use `dispatch` for that.

## Nested construction

Annotate fields with concrete dataclasses and typed containers. Nightjar builds
all nested values before passing the configuration to the implementation:

```python
from __future__ import annotations

from dataclasses import dataclass
from nightjar import dispatch, register, to_dict


@dataclass
class Endpoint:
    port: int


@dataclass
class Network:
    primary: Endpoint
    replicas: list[Endpoint]
    named: dict[str, Endpoint]


@dataclass
class ServerConfig:
    network: Network
    kind: str = "server"


@register(kind="server")
@dataclass
class Server:
    config: ServerConfig


server = dispatch(ServerConfig, {
    "kind": "server",
    "network": {
        "primary": {"port": "8000"},
        "replicas": [{"port": "8001"}],
        "named": {"backup": {"port": "8002"}},
    },
})
assert server.config.network.primary == Endpoint(8000)
assert server.config.network.replicas == [Endpoint(8001)]
assert server.config.network.named["backup"] == Endpoint(8002)
assert dispatch(ServerConfig, to_dict(server.config)).config == server.config
```

Containers can be nested further, such as `dict[str, list[Endpoint]]` or
`list[dict[str, Endpoint]]`. Dictionary keys are converted using their annotated
type too. Bare `list` and `dict` annotations do not specify dataclass types for
their contents.

Existing dataclass instances are preserved. Missing fields use dataclass defaults
when available; undeclared keys in nested dataclasses raise `TypeError`.
This builds nested configuration values. It does not invoke registrations for
nested implementations, and calling `ServerConfig(...)` directly uses the normal
dataclass constructor without Nightjar conversion.

## Pydantic models

Use your installed Pydantic version's model definitions and validators. Nightjar
delegates model validation to that version and dumps v2 models with
`model_dump(mode="python")` or v1 models with `dict()`. Pydantic dataclasses also
use their native validation. Their extra-field behavior follows Pydantic
configuration; Nightjar's plain-dataclass rejection rule does not override it.
Configure Pydantic models with `extra="forbid"` to reject undeclared keys.

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
