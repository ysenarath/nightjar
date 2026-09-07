"""Regression tests for Nightjar's conversion behavior."""

import unittest
from collections import namedtuple
from dataclasses import dataclass
from typing import ForwardRef, List, Optional

from nightjar import from_dict, to_dict


@dataclass
class Inner:
    x: int


@dataclass
class Weird:
    x: int

    def __post_init__(self):
        # Raises IndexError for reasons unrelated to from_dict's
        # "no type args" fallback logic.
        empty = []
        empty[0]


@dataclass
class Point:
    x: int
    y: int


class TestUnionForwardRefNamespacePropagation(unittest.TestCase):
    """Issue: Union recursion in from_dict drops globalns/localns."""

    def test_optional_forwardref_resolved_via_localns(self):
        typ = Optional[ForwardRef("Inner")]
        result = from_dict(typ, {"x": 1}, localns={"Inner": Inner})
        self.assertEqual(result, Inner(x=1))


class TestListConversionDoesNotSwallowIndexError(unittest.TestCase):
    """Issue: from_dict's List handling catches IndexError too broadly."""

    def test_unrelated_index_error_is_not_swallowed(self):
        with self.assertRaises(IndexError):
            from_dict(List[Weird], [{"x": 1}, {"x": 2}])


class TestBoolCoercion(unittest.TestCase):
    """Issue: from_dict(bool, "false") returns True due to bool("false")."""

    def test_string_false_converts_to_false(self):
        self.assertFalse(from_dict(bool, "false"))

    def test_string_true_converts_to_true(self):
        self.assertTrue(from_dict(bool, "true"))


class TestNamedTupleSerialization(unittest.TestCase):
    """Issue: to_dict's namedtuple branch is dead code (identical to plain tuple)."""

    def test_namedtuple_preserves_field_names(self):
        NamedPoint = namedtuple("NamedPoint", ["x", "y"])
        result = to_dict(NamedPoint(x=1, y=2))
        self.assertEqual(result, {"x": 1, "y": 2})


class TestUnknownDataclassKeys(unittest.TestCase):
    """Issue: from_dict's dataclass branch doesn't filter unknown keys."""

    def test_unknown_keys_are_ignored(self):
        result = from_dict(Point, {"x": 1, "y": 2, "z": 99})
        self.assertEqual(result, Point(x=1, y=2))


if __name__ == "__main__":
    unittest.main()
