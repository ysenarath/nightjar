"""Composable field predicates and registries for configuration dispatch."""

from __future__ import annotations

import functools
import operator
from collections import defaultdict
from collections.abc import Callable
from dataclasses import MISSING
from typing import Any, Generic, Type, TypeVar

from nightjar.annotations import get_dataclass_type_hints
from nightjar.conversion import from_dict, to_dict

F = Callable[..., Any]
T = TypeVar("T")


def _getattr(cls: type, attr: str):
    """Read a class attribute, following annotated dataclass types in dotted paths."""
    if "." not in attr:
        return getattr(cls, attr)
    parts = attr.split(".")
    for part in parts[:-1]:
        cls = get_dataclass_type_hints(cls)[part]
    part = parts[-1]
    return getattr(cls, part, None)


def _getitem(obj: dict, key: str) -> Any:
    """Read a mapping key or dotted path; a missing plain key returns None."""
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
    """Composable value expression used to select configurations.

    Comparisons, & and | create expression objects; ~ negates an expression.
    Operands are evaluated eagerly when the resulting expression is evaluated.
    """

    __hash__ = None

    def evaluate(self, val: dict) -> bool:
        """Evaluate the expression against input data; subclasses must implement it."""
        raise NotImplementedError

    def __and__(self, other: Expression) -> Expression:
        """Build an eager conjunction with another operand."""
        return FunctionExpression(operator.and_, self, other)

    def __rand__(self, other: Expression) -> Expression:
        """Build an eager conjunction with the other operand first."""
        return FunctionExpression(operator.and_, other, self)

    def __or__(self, other: Expression) -> Expression:
        """Build an eager disjunction with another operand."""
        return FunctionExpression(operator.or_, self, other)

    def __invert__(self) -> Expression:
        """Build the logical negation of this expression."""
        return FunctionExpression(operator.not_, self)

    def eq(self, value) -> Expression:
        """Build an equality comparison with another expression or literal value."""
        return FunctionExpression(operator.eq, self, value)

    def __eq__(self, value) -> Expression:
        """Build an equality expression."""
        return self.eq(value)

    def __ne__(self, value) -> Expression:
        """Build an inequality expression."""
        return FunctionExpression(operator.ne, self, value)

    def __gt__(self, value) -> Expression:
        """Build a greater-than expression."""
        return FunctionExpression(operator.gt, self, value)

    def __ge__(self, value) -> Expression:
        """Build a greater-than-or-equal expression."""
        return FunctionExpression(operator.ge, self, value)

    def __lt__(self, value) -> Expression:
        """Build a less-than expression."""
        return FunctionExpression(operator.lt, self, value)

    def __le__(self, value) -> Expression:
        """Build a less-than-or-equal expression."""
        return FunctionExpression(operator.le, self, value)

    def contains(self, value) -> Expression:
        """Test whether this expression's value is contained in the supplied container."""
        return FunctionExpression(operator.contains, value, self)


class Field(Expression):
    """Read a top-level input key for a dispatch expression.

    Missing keys return default, which is None unless supplied explicitly.
    Use dataclasses.MISSING as the default to require the key. Field names
    are literal keys; Field itself does not traverse dotted paths.
    """

    name: str
    default: Any

    def __init__(self, name: str, default: Any = None) -> None:
        """Store the input key and the value to use when it is missing."""
        self.name = name
        self.default = default

    def exists(self) -> Expression:
        """Build a key-presence test, including keys whose value is None."""
        return FieldExistsExpression(self.name)

    def evaluate(self, val: dict) -> Any:
        """Read the field or its default, raising KeyError when a required key is absent."""
        if self.default is MISSING:
            return val[self.name]
        return val.get(self.name, self.default)

    @property
    def str(self) -> StringField:
        """Return a string-oriented view of this field with the same default."""
        return StringField(self.name, self.default)


class StringField(Field):
    """Convert non-None field values to strings before applying string operations."""

    def lower(self) -> Expression:
        """Build an expression applying str.lower to the field value."""
        return FunctionExpression(str.lower, self)

    def upper(self) -> Expression:
        """Build an expression applying str.upper to the field value."""
        return FunctionExpression(str.upper, self)

    def strip(self) -> Expression:
        """Build an expression stripping surrounding whitespace from the field value."""
        return FunctionExpression(str.strip, self)

    def startswith(self, prefix: str) -> Expression:
        """Build a prefix test for the field value."""
        return FunctionExpression(str.startswith, self, prefix)

    def endswith(self, suffix: str) -> Expression:
        """Build a suffix test for the field value."""
        return FunctionExpression(str.endswith, self, suffix)

    def eq(self, value: str, case: bool = True) -> Expression:
        """Build a string equality test; case=False compares lowercase values."""
        if case:
            return super().eq(value)
        return self.equals_ignore_case(value)

    def equals_ignore_case(self, value: str) -> Expression:
        """Build equality between the lowercase field and comparison value."""
        return FunctionExpression(operator.eq, self.lower(), value.lower())

    def evaluate(self, val: dict) -> Any:
        """Return the field as a string, preserving None."""
        result = super().evaluate(val)
        if result is None:
            return result
        return str(result)


class FieldExistsExpression(Expression):
    """Expression testing whether an input key is present."""

    field: str

    def __init__(self, field: str) -> None:
        """Store the key whose presence will be checked."""
        self.field = field

    def evaluate(self, val: dict) -> bool:
        """Return whether the key is present, regardless of its value."""
        return self.field in val


class FunctionExpression(Expression):
    """Apply an operator to evaluated expressions and literal operands.

    Operator exceptions produce False. Exceptions while evaluating operands
    propagate to the caller.
    """

    operator: F
    operands: list[Expression]

    def __init__(self, operator: F, *operands: Expression) -> None:
        """Store an operator and its expression or literal operands."""
        self.operator = operator
        self.operands = list(operands)

    def evaluate(self, val: dict) -> Any:
        """Evaluate all operands and apply the operator, returning False on operator errors."""
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
    """Expression returning the truth value of a stored constant."""

    value: Any

    def __init__(self, value: Any = True) -> None:
        """Store the constant; the default produces an always-true expression."""
        self.value = value

    def evaluate(self, val: dict) -> bool:
        """Return the truth value of the constant, ignoring input data."""
        return bool(self.value)


def create_expression(constraint: Expression | Any) -> Expression:
    """Preserve expressions, wrap literal constraints, and treat MISSING as True."""
    if constraint is MISSING:
        return LiteralExpression(True)
    elif isinstance(constraint, Expression):
        return constraint
    return LiteralExpression(constraint)


class DispatchRegistry(Generic[T]):
    """Select registered configuration classes using attributes and predicates.

    Discriminator attributes narrow candidates by class-level values. Each
    candidate's constraint must also pass, and exactly one class must match.
    With no discriminator attributes, all registered constraints are tested.
    """

    def __init__(self, attrs: list[str] | str | None = None):
        """Create a registry with zero, one, or multiple discriminator attribute names."""
        self.attrs = attrs
        self.constraints: dict[Type, Expression] = {}
        self.column_value_types: dict[str, dict[Any, set[Type]]] = defaultdict(
            functools.partial(defaultdict, set)
        )

    @property
    def attrs(self) -> list[str]:
        """Get or set discriminator names; changing them does not rebuild existing indexes."""
        return self._attrs

    @attrs.setter
    def attrs(self, value: list[str] | str | None) -> None:
        """Get or set discriminator names; changing them does not rebuild existing indexes."""
        if value is None:
            value = []
        elif isinstance(value, str):
            value = [value]
        self._attrs = list(value)

    def register(self, cls, constraint: Expression | Any = MISSING) -> None:
        # get class attribute values for dispatch attributes
        """Index a class and store its selection constraint.

        An explicit constraint overrides __match__. Otherwise the class's
        __match__ expression is used when present; a missing constraint accepts
        all input. Discriminator values must be hashable.
        """
        for a in self.attrs:
            val = _getattr(cls, a)
            self.column_value_types[a][val].add(cls)
        # if there is any additional constraints, keep track of them
        if hasattr(cls, "__match__") and constraint is MISSING:
            constraint = getattr(cls, "__match__", None)
        self.constraints[cls] = create_expression(constraint)

    def load(self, val: dict, globalns: Any = None, localns: Any = None) -> T:
        """Select a class, convert its known fields, and construct an instance.

        Unknown input keys are ignored. Namespaces are forwarded to field-value
        conversion. Selection, conversion, and constructor errors propagate.
        """
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
        """Return the unique class matching discriminator values and constraints.

        Raises ValueError when no class or multiple classes match. Dotted
        attribute paths traverse the input mappings.
        """
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
        """Serialize an instance and add top-level discriminator attributes.

        Root dispatch is disabled to avoid re-entering this registry. Nested
        values retain dispatch; dotted discriminator paths are not added.
        """
        data = to_dict(obj, dispatch=False)
        for a in self.attrs:
            if "." in a:
                # these do not belong in the data for this object
                continue
            data[a] = getattr(obj, a)
        return data
