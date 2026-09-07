import unittest
from dataclasses import dataclass
from datetime import date, datetime, time
from decimal import Decimal
from pathlib import Path
from typing import Annotated, Any, Literal, Union
from uuid import UUID

import pydantic
from pydantic import BaseModel, Field, ValidationError

from nightjar import converter_registry, from_dict, to_dict


class Item(BaseModel):
    count: int
    enabled: bool = True


class Cat(BaseModel):
    kind: Literal["cat"]
    lives: int


class Dog(BaseModel):
    kind: Literal["dog"]
    friendly: bool


@dataclass
class Basket:
    items: list[Item]


if hasattr(pydantic, "field_validator"):
    _before_count = pydantic.field_validator("count", mode="before")
else:
    _before_count = pydantic.validator("count", pre=True, allow_reuse=True)


@pydantic.dataclasses.dataclass
class ValidatedItem:
    count: int

    @_before_count
    def normalize_count(cls, value):  # noqa: N805 - Pydantic class validator
        return 1 if value == "one" else value


class TestPydanticIntegration(unittest.TestCase):
    def test_dataclass_dump_does_not_resolve_annotations(self):
        @dataclass
        class Unresolved:
            value: "UnavailableType"  # noqa: F821 - encoding needs only values

        self.assertEqual(to_dict(Unresolved(3)), {"value": 3})

    def test_pydantic_dataclass_runs_its_own_validation_first(self):
        item = from_dict(ValidatedItem, {"count": "one"})
        self.assertIsInstance(item, ValidatedItem)
        self.assertEqual(item.count, 1)
        self.assertEqual(to_dict(item), {"count": 1})
        with self.assertRaises(ValidationError):
            from_dict(ValidatedItem, {"count": "invalid"})

    def test_special_types_use_pydantic(self):
        value = {"nested": [1]}
        self.assertIs(from_dict(Any, value), value)
        self.assertEqual(from_dict(Literal["yes", "no"], "yes"), "yes")
        self.assertIsNone(from_dict(None, None))
        with self.assertRaises(ValidationError):
            from_dict(Literal["yes", "no"], "maybe")
        with self.assertRaises(ValidationError):
            from_dict(type(None), 1)

    def test_model_validation_and_serialization(self):
        item = from_dict(Item, {"count": "4", "enabled": "false"})
        self.assertIsInstance(item, Item)
        self.assertEqual(to_dict(item), {"count": 4, "enabled": False})
        self.assertIs(from_dict(Item, item), item)
        with self.assertRaises(ValidationError):
            from_dict(Item, {"count": "invalid"})

    def test_models_nested_in_dataclasses_and_containers(self):
        basket = from_dict(Basket, {"items": [{"count": "3"}]})
        self.assertIsInstance(basket.items[0], Item)
        self.assertEqual(
            to_dict({"basket": basket}),
            {"basket": {"items": [{"count": 3, "enabled": True}]}},
        )

    def test_scalar_validation(self):
        identifier = "12345678-1234-5678-1234-567812345678"
        cases = [
            (UUID, identifier, UUID(identifier)),
            (Decimal, "1.25", Decimal("1.25")),
            (date, "2026-09-07", date(2026, 9, 7)),
            (datetime, "2026-09-07T12:30:00", datetime(2026, 9, 7, 12, 30)),  # noqa: DTZ001
            (time, "12:30:00", time(12, 30)),
            (Path, "example.txt", Path("example.txt")),
            (bool, "yes", True),
        ]
        for typ, raw, expected in cases:
            with self.subTest(typ=typ):
                self.assertEqual(from_dict(typ, raw), expected)

    def test_annotated_constraints(self):
        positive = Annotated[int, Field(gt=0)]
        self.assertEqual(from_dict(positive, "3"), 3)
        with self.assertRaises(ValidationError):
            from_dict(positive, -1)

    def test_pydantic_discriminated_union(self):
        pet = Annotated[Union[Cat, Dog], Field(discriminator="kind")]
        result = from_dict(pet, {"kind": "cat", "lives": "9"})
        self.assertIsInstance(result, Cat)
        self.assertEqual(result.lives, 9)

    def test_generic_arguments_do_not_leak_into_children(self):
        self.assertEqual(from_dict(list[list], [[1, 2]]), [[1, 2]])
        self.assertEqual(from_dict(dict[str, list], {"x": [1]}), {"x": [1]})
        self.assertEqual(from_dict(set[int], ["1", "2"]), {1, 2})
        self.assertEqual(from_dict(list[set], [[1, 2]]), [{1, 2}])

    def test_custom_converter_overrides_pydantic(self):
        converter = converter_registry.register_type(
            UUID, decode=lambda typ, value: typ(int=int(value))
        )
        try:
            self.assertEqual(from_dict(UUID, "7"), UUID(int=7))
        finally:
            converter_registry.unregister(converter)

    @unittest.skipUnless(hasattr(pydantic, "TypeAdapter"), "Pydantic v2 only")
    def test_v1_model_inside_v2_installation(self):
        from pydantic.v1 import (  # noqa: PLC0415 - v2-only test
            BaseModel as LegacyBaseModel,
        )

        class LegacyItem(LegacyBaseModel):
            count: int

        result = from_dict(LegacyItem, {"count": "5"})
        self.assertIsInstance(result, LegacyItem)
        self.assertEqual(to_dict(result), {"count": 5})


if __name__ == "__main__":
    unittest.main()
