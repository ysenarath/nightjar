from __future__ import annotations

import functools
import operator
from collections import defaultdict
from collections.abc import Callable
from dataclasses import MISSING
from typing import Any, Generic, Type, TypeVar

from nightjar.serializers import from_dict, to_dict
from nightjar.utils import get_dataclass_type_hints

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
        return obj.get(key)
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
        return FunctionExpression(operator.not_, self)

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
    default: Any

    def __init__(self, name: str, default: Any = None) -> None:
        self.name = name
        self.default = default

    def exists(self) -> Expression:
        return FieldExistsExpression(self.name)

    def evaluate(self, val: dict) -> Any:
        if self.default is MISSING:
            return val[self.name]
        return val.get(self.name, self.default)

    @property
    def str(self) -> StringField:
        return StringField(self.name, self.default)


class StringField(Field):
    def lower(self) -> Expression:
        return FunctionExpression(str.lower, self)

    def upper(self) -> Expression:
        return FunctionExpression(str.upper, self)

    def strip(self) -> Expression:
        return FunctionExpression(str.strip, self)

    def startswith(self, prefix: str) -> Expression:
        return FunctionExpression(str.startswith, self, prefix)

    def endswith(self, suffix: str) -> Expression:
        return FunctionExpression(str.endswith, self, suffix)

    def eq(self, value: str, case: bool = True) -> Expression:
        if case:
            return super().eq(value)
        return self.equals_ignore_case(value)

    def equals_ignore_case(self, value: str) -> Expression:
        return FunctionExpression(operator.eq, self.lower(), value.lower())

    def evaluate(self, val: dict) -> Any:
        result = super().evaluate(val)
        if result is None:
            return result
        return str(result)


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

    def evaluate(self, val: dict) -> Any:
        operands = []
        for operand in self.operands:
            if isinstance(operand, Expression):
                operand = operand.evaluate(val)
            operands.append(operand)
        try:
            return self.operator(*operands)
        except Exception:
            return False


class LiteralExpression(Expression):
    value: Any

    def __init__(self, value: Any = True) -> None:
        self.value = value

    def evaluate(self, val: dict) -> bool:
        return bool(self.value)


def create_expression(constraint: Expression | Any) -> Expression:
    if constraint is MISSING:
        return LiteralExpression(True)
    elif isinstance(constraint, Expression):
        return constraint
    return LiteralExpression(constraint)


class DispatchRegistry(Generic[T]):
    def __init__(self, attrs: list[str] | str | None = None):
        self.attrs = attrs
        self.constraints: dict[Type, Expression] = {}
        self.column_value_types: dict[str, dict[Any, set[Type]]] = defaultdict(
            functools.partial(defaultdict, set)
        )

    @property
    def attrs(self) -> list[str]:
        return self._attrs

    @attrs.setter
    def attrs(self, value: list[str] | str | None) -> None:
        if value is None:
            value = []
        elif isinstance(value, str):
            value = [value]
        self._attrs = list(value)

    def register(self, cls, constraint: Expression | Any = MISSING) -> None:
        # get class attribute values for dispatch attributes
        for a in self.attrs:
            val = _getattr(cls, a)
            self.column_value_types[a][val].add(cls)
        # if there is any additional constraints, keep track of them
        if hasattr(cls, "__match__") and constraint is MISSING:
            constraint = getattr(cls, "__match__", None)
        self.constraints[cls] = create_expression(constraint)

    def load(self, val: dict, globalns: Any = None, localns: Any = None) -> T:
        val = dict(val).copy()
        klass = self.resolve_type(val)
        field_types = get_dataclass_type_hints(klass)
        kwargs = {
            k: from_dict(
                field_types.get(k, Any),
                v,
                globalns=globalns,
                localns=localns,
            )
            for k, v in val.items()
            if k in field_types
        }
        return klass(**kwargs)

    def resolve_type(self, val: dict) -> Any:
        candidates: set[Type] | None = None
        for a in self.attrs:
            attr_val = _getitem(val, a)
            classes_for_value = self.column_value_types[a].get(attr_val, set())
            if candidates is None:
                candidates = set().union(classes_for_value)
            else:
                candidates = candidates.intersection(classes_for_value)
            if not candidates:
                break
        if candidates is None:
            candidates = set()
            for klass, constraint in self.constraints.items():
                if not constraint.evaluate(val):
                    continue
                candidates.add(klass)
        else:
            for klass in list(candidates):
                if klass not in self.constraints:
                    continue  # no constraint -- keep it
                constraint = self.constraints[klass]
                if constraint.evaluate(val):
                    continue  # matches constraint -- keep it
                candidates.discard(klass)
        n_candidates = len(candidates)
        if n_candidates > 1:
            matching_class_names = ", ".join([c.__name__ for c in candidates])
            # one sentence error message without colons or line breaks
            msg = f"multiple classes ({matching_class_names}) match the given data ({val})"
            raise ValueError(msg)
        if n_candidates == 0:
            msg = "no class matching the given data"
            raise ValueError(msg)
        return candidates.pop()

    def dump(self, obj: Any) -> dict:
        data = to_dict(obj, dispatch=False)
        for a in self.attrs:
            if "." in a:
                # these do not belong in the data for this object
                continue
            data[a] = getattr(obj, a)
        return data
