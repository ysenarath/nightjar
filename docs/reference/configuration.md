# Registration and dispatch

Import these functions from `nightjar`. Configuration types can be plain
dataclasses or Pydantic models; implementations need no Nightjar base class.

Overlapping registrations are allowed. Ambiguity is checked when `dispatch`
is called; registration order does not break ties. See the
[ambiguity example](../guides/dispatch.md#ambiguity-is-checked-at-dispatch-time).

::: nightjar.dispatching.register

::: nightjar.dispatching.dispatch
