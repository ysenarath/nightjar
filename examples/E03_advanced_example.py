from dataclasses import dataclass

from nightjar import BaseConfig, Field, dispatch, register


class VehicleConfig(BaseConfig): ...


class CarConfig(VehicleConfig):
    __match__ = Field("type").str.eq("car", case=False) | (
        Field("num_doors") == 4
    )

    type: str = "car"
    num_doors: int = 4


@register(CarConfig)
@dataclass
class Car:
    config: CarConfig


class VanConfig(VehicleConfig):
    __match__ = (
        Field("type").str.eq("van", case=False) & ~Field("new_attr").exists()
    )

    type: str = "van"


class AltVanConfig(VehicleConfig):
    __match__ = Field("type").str.eq("van", case=False) & (
        Field("new_attr").exists()
    )

    type: str = "van"
    new_attr: int = 10


@register(AltVanConfig, VanConfig)
@dataclass
class Van:
    config: VanConfig | AltVanConfig


def test_default_car():
    v = dispatch(VehicleConfig, {"type": "CAR"})
    assert isinstance(v, Car)


def test_car():
    v = dispatch(VehicleConfig, {"num_doors": 4})
    assert isinstance(v, Car)


def test_van():
    v = dispatch(VehicleConfig, {"type": "van"})
    assert isinstance(v, Van)
    assert isinstance(v.config, VanConfig)


def test_alt_van():
    v = dispatch(VehicleConfig, {"type": "van", "new_attr": 5})
    assert isinstance(v, Van)
    assert isinstance(v.config, AltVanConfig)
    assert v.config.new_attr == 5


if __name__ == "__main__":
    test_default_car()
    test_car()
    test_van()
    test_alt_van()
