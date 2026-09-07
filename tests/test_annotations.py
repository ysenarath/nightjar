import unittest
from dataclasses import InitVar, dataclass
from functools import wraps
from types import ModuleType
from typing import ClassVar

from nightjar.annotations import get_annotations, get_dataclass_type_hints


class TestGetAnnotations(unittest.TestCase):
    def test_wrapped_callable_uses_original_namespace(self):
        namespace = {"Alias": int}
        exec("def original(value: 'Alias'): pass", namespace)  # noqa: S102
        original = namespace["original"]

        @wraps(original)
        def wrapper(*args, **kwargs):
            return original(*args, **kwargs)

        self.assertEqual(get_annotations(wrapper), {"value": int})
        self.assertIs(
            get_annotations(wrapper, eval_str=False), wrapper.__annotations__
        )
        self.assertEqual(
            get_annotations(wrapper, {"Alias": str}), {"value": str}
        )

    def test_class_annotations_and_inheritance(self):
        class Parent:
            value: int

        class Child(Parent):
            pass

        self.assertEqual(get_annotations(Parent), {"value": int})
        self.assertEqual(get_annotations(Child), {})

    def test_string_evaluation_modes(self):
        module = ModuleType("annotation_test")
        module.__annotations__ = {"value": "Alias"}
        namespace = {"Alias": int}

        self.assertEqual(
            get_annotations(module, {}, namespace), {"value": int}
        )
        self.assertEqual(
            get_annotations(module, eval_str=False), {"value": "Alias"}
        )

        module.__annotations__["other"] = str
        self.assertEqual(
            get_annotations(module), {"value": "Alias", "other": str}
        )
        self.assertEqual(
            get_annotations(module, {}, namespace, eval_str=True),
            {"value": int, "other": str},
        )


class TestDataclassTypeHints(unittest.TestCase):
    def test_inherited_fields_and_namespace_resolution(self):
        @dataclass
        class Parent:
            value: "Alias"  # noqa: F821 - resolved through localns below
            shared: ClassVar[int] = 1

        @dataclass
        class Child(Parent):
            temporary: InitVar[str]
            label: str = ""

        hints = get_dataclass_type_hints(Child, localns={"Alias": int})
        self.assertEqual(hints, {"value": int, "label": str})
        self.assertEqual(list(hints), ["value", "label"])
