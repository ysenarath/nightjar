from __future__ import annotations

import sys
import typing
import unittest
from dataclasses import dataclass
from types import ModuleType
from typing import Annotated, ClassVar, ForwardRef, Literal, Optional, Union

from nightjar import AutoModule, BaseConfig, BaseModule, from_dict
from nightjar.annotations import get_annotations, get_dataclass_type_hints


@dataclass
class Payload:
    values: list[int | str] | None


@dataclass
class NestedPayload:
    values: list["int | str"]  # noqa: UP037 - exercise nested string resolution
    label: Literal["int | str"]
    tagged: Annotated[int | str, "int | str"]


class UnionConfig(BaseConfig, dispatch=["kind"]):
    kind: ClassVar[str]


class UnionModule(BaseModule):
    config: UnionConfig


class AutoUnionModule(AutoModule):
    pass


class ConcreteConfig(UnionConfig):
    kind: ClassVar[str] = "concrete"
    values: list[str] | None


class ConcreteModule(UnionModule):
    config: ConcreteConfig


class TestPostponedUnions(unittest.TestCase):
    def test_dataclass_decode(self):
        self.assertEqual(from_dict(Payload, {"values": None}), Payload(None))
        self.assertEqual(
            from_dict(Payload, {"values": [1, "word"]}), Payload([1, "word"])
        )

    def test_nested_quoted_types_and_metadata(self):
        hints = get_dataclass_type_hints(NestedPayload)
        if sys.version_info < (3, 10):
            self.assertEqual(hints["values"], list[Union[int, str]])
        else:
            self.assertEqual(hints, typing.get_type_hints(NestedPayload))
        self.assertEqual(hints["label"], Literal["int | str"])
        self.assertEqual(hints["tagged"], Union[int, str])

    def test_dispatch_with_postponed_config(self):
        config = UnionConfig.from_dict({"kind": "concrete", "values": None})
        module = AutoUnionModule(config)
        self.assertIsInstance(module, ConcreteModule)
        self.assertIsNone(module.config.values)

    def test_string_and_forwardref_namespaces(self):
        namespace = {"Alias": Payload}
        for annotation in ("Alias | None", ForwardRef("Alias | None")):
            with self.subTest(annotation=annotation):
                self.assertEqual(
                    from_dict(annotation, {"values": None}, localns=namespace),
                    Payload(None),
                )
                self.assertIsNone(
                    from_dict(annotation, None, localns=namespace)
                )

    def test_evaluation_policy_and_value_expressions(self):
        module = ModuleType("union_policy")
        module.__annotations__ = {"value": "int | None"}
        self.assertEqual(get_annotations(module), {"value": Optional[int]})
        self.assertEqual(
            get_annotations(module, eval_str=False), {"value": "int | None"}
        )
        module.__annotations__["other"] = str
        self.assertEqual(get_annotations(module), module.__annotations__)
        self.assertEqual(
            get_annotations(module, eval_str=True),
            {"value": Optional[int], "other": str},
        )
        module.__annotations__ = {
            "quoted": "'int | None'",
            "literal": "Literal['int | str']",
            "bits": "1 | 2",
        }
        self.assertEqual(
            get_annotations(module, {"Literal": Literal}),
            {
                "quoted": "int | None",
                "literal": Literal["int | str"],
                "bits": 3,
            },
        )

    def test_recursive_alias_terminates(self):
        alias = list[ForwardRef("Tree | int")]
        result = from_dict("Tree", [1, [2]], localns={"Tree": alias})
        self.assertEqual(result, [1, [2]])

    def test_errors_propagate(self):
        with self.assertRaises(NameError):
            get_annotations(ConcreteModule, {})
        with self.assertRaises(NameError):
            from_dict(ForwardRef("Missing | None"), None)

    @unittest.skipUnless(
        sys.version_info < (3, 10), "Python 3.9 isolation check"
    )
    def test_stdlib_typing_is_not_patched(self):
        with self.assertRaises(TypeError):
            typing.get_type_hints(Payload)
        self.assertIn("values", get_dataclass_type_hints(Payload))


if __name__ == "__main__":
    unittest.main()
