from __future__ import annotations

import operator
from collections.abc import Callable
from dataclasses import dataclass, fields
from typing import Any, Generic, Type, TypeVar

from nightjar.helpers import get_dataclass_type_hints
from nightjar.types import from_dict, to_dict

F = Callable[..., Any]
T = TypeVar("T")


def _getattr(cls: type, attr: str):
    if "." not in attr:
        return getattr(cls, attr)
    parts = attr.split(".")
    for part in parts[:-1]:
        cls = get_dataclass_type_hints(cls)[part]
    part = parts[-1]
    return getattr(cls, part, None)


def _getitem(obj: dict, key: str) -> Any:
    msg = f"key '{key}' not found in {obj}"
    if "." in key:
        parts = key.split(".")
        for part in parts:
            obj = obj[part]
        return obj
    try:
        return obj.pop(key)
    except KeyError:
        raise KeyError(msg) from None


class Expression:
    __hash__ = None

    def evaluate(self, val: dict) -> bool:
        raise NotImplementedError

    def __and__(self, other: Expression) -> Expression:
        return FunctionExpression(operator.and_, self, other)

    def __rand__(self, other: Expression) -> Expression:
        return FunctionExpression(operator.and_, other, self)

    def __or__(self, other: Expression) -> Expression:
        return FunctionExpression(operator.or_, self, other)

    def __invert__(self) -> Expression:
        return FunctionExpression(operator.inv, self)

    def eq(self, value) -> Expression:
        return FunctionExpression(operator.eq, self, value)

    def __eq__(self, value) -> Expression:
        return self.eq(value)

    def __ne__(self, value) -> Expression:
        return FunctionExpression(operator.ne, self, value)

    def __gt__(self, value) -> Expression:
        return FunctionExpression(operator.gt, self, value)

    def __ge__(self, value) -> Expression:
        return FunctionExpression(operator.ge, self, value)

    def __lt__(self, value) -> Expression:
        return FunctionExpression(operator.lt, self, value)

    def __le__(self, value) -> Expression:
        return FunctionExpression(operator.le, self, value)

    def contains(self, value) -> Expression:
        return FunctionExpression(operator.contains, value, self)


class Field(Expression):
    name: str

    def __init__(self, name: str) -> None:
        self.name = name

    def exists(self) -> Expression:
        return FieldExistsExpression(self.name)

    def evaluate(self, val: dict) -> Any:
        return val[self.name]


class FieldExistsExpression(Expression):
    field: str

    def __init__(self, field: str) -> None:
        self.field = field

    def evaluate(self, val: dict) -> bool:
        return self.field in val


class FunctionExpression(Expression):
    operator: F
    operands: list[Expression]

    def __init__(self, operator: F, *operands: Expression) -> None:
        self.operator = operator
        self.operands = list(operands)

    def evaluate(self, val: dict) -> bool:
        operands = []
        for operand in self.operands:
            if isinstance(operand, Expression):
                operand = operand.evaluate(val)
            operands.append(operand)
        return self.operator(*operands)


class ObjectFactory:
    def __init__(self):
        self.classes: list[Type] = []
        self.constraints: list[Expression] = []

    def register(
        self, cls: Type, constraint: Expression | None = None
    ) -> None:
        self.classes.append(cls)
        if constraint is None:
            constraint = getattr(cls, "__match__", None)
            if constraint is None:
                msg = f"No constraint provided for class {cls.__name__}"
                raise ValueError(msg)
        self.constraints.append(constraint)
        return cls

    def load(self, val: dict) -> Any:
        for cls, constraint in zip(self.classes, self.constraints):
            if constraint.evaluate(val):
                field_names = {f.name for f in fields(cls)}
                filtered_val = {
                    k: v for k, v in val.items() if k in field_names
                }
                return cls(**filtered_val)
        msg = "No matching class found for the given data."
        raise ValueError(msg)


class DispatchRegistry(Generic[T]):
    def __init__(self, attrs: list[str] | str):
        self.types = {}
        if isinstance(attrs, str):
            attrs = [attrs]
        self.attrs = attrs

    def register(self, cls):
        self.types[tuple(_getattr(cls, a) for a in self.attrs)] = cls

    def load(self, val: dict, globalns: Any = None, localns: Any = None) -> T:
        val = dict(val).copy()
        idv = tuple(_getitem(val, a) for a in self.attrs)
        typ = self.types[idv]
        field_types = get_dataclass_type_hints(typ)
        kwargs = {
            k: from_dict(
                field_types.get(k, Any),
                v,
                globalns=globalns,
                localns=localns,
            )
            for k, v in val.items()
        }
        return typ(**kwargs)

    def dump(self, obj: Any) -> dict:
        data = to_dict(obj, dispatch=False)
        for a in self.attrs:
            if "." in a:
                # these do not belong in the data for this object
                continue
            data[a] = getattr(obj, a)
        return data


def _make_registry() -> ObjectFactory:
    registry = ObjectFactory()

    @registry.register
    @dataclass
    class Car:
        __match__ = (Field("wheels") == 4) & Field("engine").exists()

        wheels: int
        engine: str
        doors: int = 4

    @registry.register
    @dataclass
    class Motorcycle:
        __match__ = (Field("wheels") == 2) & Field("engine").exists()

        wheels: int
        engine: str

    @registry.register
    @dataclass
    class Bicycle:
        __match__ = (Field("wheels") == 2) & Field("frame").exists()

        wheels: int
        frame: str

    @registry.register
    @dataclass
    class Truck:
        __match__ = (Field("wheels") == 6) & Field("engine").exists()

        wheels: int
        engine: str
        cargo: float = 0.0

    test_cases = [
        {"wheels": 4, "engine": "V6", "doors": 2},
        {"wheels": 2, "engine": "inline-2"},
        {"wheels": 2, "frame": "carbon"},
        {"wheels": 6, "engine": "diesel", "cargo": 5000},
    ]

    for data in test_cases:
        result = registry.load(data)
        print(result.__class__.__name__)
        for f in fields(result.__class__):
            print(f"+ {f.name} = {getattr(result, f.name)}")
        print()


if __name__ == "__main__":
    main()
