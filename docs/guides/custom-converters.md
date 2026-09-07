# Custom converters

The shared `converter_registry` contains Nightjar's built-in conversion rules.
Register a leaf type with encode and decode functions:

```python
from uuid import UUID
from nightjar import converter_registry, from_dict, to_dict

converter = converter_registry.register_type(
    UUID,
    encode=str,
    decode=lambda typ, value: typ(value),
)

try:
    text = "12345678-1234-5678-1234-567812345678"
    value = from_dict(UUID, text)
    assert isinstance(value, UUID)
    assert to_dict(value) == text
finally:
    converter_registry.unregister(converter)
```

`register_type` prepends rules by default. The first matching converter handles
the value, allowing custom rules to override built-ins. Registrations affect the
shared registry; unregister temporary rules when they are no longer needed.

For rules that inspect generic arguments or recursively convert children,
subclass `Converter`. Implement `matches_encode` and `encode`,
`matches_decode` and `decode`, or both pairs. Use `ctx.encode(child)` and
`ctx.decode(child_type, value)` to recurse through the same registry.
Register the instance with `converter_registry.register(rule, prepend=True)`
when it should take priority over built-ins.

A new `ConverterRegistry()` starts empty. Use the shared `converter_registry`
when extending standard Nightjar behavior.

See the [conversion reference](../reference/conversion.md) for signatures and
context behavior.
