import unittest
from dataclasses import dataclass
from typing import ClassVar, Union

from nightjar import Field, dispatch, register


@dataclass
class VehicleConfig:
    type: ClassVar[str]


@dataclass
class CarConfig(VehicleConfig):
    type: ClassVar[str] = "car"
    num_doors: int = 4


@register(type="car")
@dataclass
class Car:
    config: CarConfig


@dataclass
class VanConfig(VehicleConfig):
    type: ClassVar[str] = "van"


@register(type="van")
@dataclass
class Van:
    config: VanConfig


class TestVehicle(unittest.TestCase):
    def test_car_with_custom_doors(self):
        config = {"type": "car", "num_doors": 2}
        car = dispatch(VehicleConfig, config)
        self.assertIsInstance(car, Car)
        assert isinstance(car, Car)  # for type checkers
        self.assertEqual(car.config.num_doors, 2)


class TestRegistrationConditions(unittest.TestCase):
    def test_expressions_and_keyword_fields_must_all_match(self):
        @dataclass
        class Config:
            count: int = 1

        @register(
            Config,
            Field("count") > 0,
            Field("count") < 10,
            when="startup",
            config="worker",
        )
        def build(config):
            return config

        data = {"count": 2, "when": "startup", "config": "worker"}
        self.assertEqual(dispatch(Config, data), Config(2))
        for change in (
            {"count": 0},
            {"count": 10},
            {"when": "stop"},
            {"config": "other"},
        ):
            with self.subTest(change=change), self.assertRaises(ValueError):
                dispatch(Config, {**data, **change})

    def test_none_requires_present_keyword(self):
        @dataclass
        class Config:
            pass

        @register(Config, when=None)
        def build(config):
            return config

        self.assertIsInstance(dispatch(Config, {"when": None}), Config)
        with self.assertRaises(ValueError):
            dispatch(Config, {})

    def test_positional_conditions_require_expressions(self):
        @dataclass
        class Config:
            pass

        for condition in (True, "kind", Config):
            with self.subTest(condition=condition), self.assertRaises(
                TypeError
            ):
                register(Config, condition)


class TestInferredRegistration(unittest.TestCase):
    def test_function_annotation_and_expression(self):
        @dataclass
        class Config:
            count: int = 1

        @register(Field("count") > 0, when="start")
        def build(config: Config):
            return config

        self.assertEqual(
            dispatch(Config, {"count": 2, "when": "start"}), Config(2)
        )

    def test_missing_annotation_rejected(self):
        with self.assertRaises(TypeError):

            @register()
            def build(config):
                return config

    def test_union_annotation_rejected(self):
        with self.assertRaises(TypeError):

            @register()
            def build(config: Union[CarConfig, VanConfig]):
                return config

    def test_inherited_and_quoted_class_annotation(self):
        class Parent:
            config: "CarConfig"

            def __init__(self, config):
                self.config = config

        @register(type="inherited")
        class Child(Parent):
            pass

        self.assertIsInstance(
            dispatch(VehicleConfig, {"type": "inherited"}), Child
        )

    def test_explicit_type_overrides_annotation(self):
        @dataclass
        class Config:
            pass

        @register(Config)
        def build(value):
            return value

        self.assertIsInstance(dispatch(Config, {}), Config)


if __name__ == "__main__":
    unittest.main()
