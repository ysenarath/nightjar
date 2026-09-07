"""Composable field predicates for configuration dispatch."""

from __future__ import annotations

import operator
from collections.abc import Callable
from dataclasses import MISSING
from typing import Any

F = Callable[..., Any]


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
