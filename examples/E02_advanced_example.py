from nightjar import AutoModule, BaseConfig, BaseModule, Field


class VehicleConfig(BaseConfig): ...


class Vehicle(BaseModule, AutoModule):
    config: VehicleConfig


class CarConfig(VehicleConfig):
    __match__ = Field("type").str.eq("car", case=False) | (
        Field("num_doors") == 4
    )

    type: str = "car"
    num_doors: int = 4


class Car(Vehicle):
    config: CarConfig


class VanConfig(VehicleConfig):
    __match__ = Field("type").str.eq("van", case=False)

    type: str = "van"


class Van(Vehicle):
    config: VanConfig


class BicycleConfig(VehicleConfig):
    __match__ = (Field("type").str.lower() == "bicycle") | (
        Field("num_doors") == 0
    )

    type: str
    num_doors: int = 0


v = Vehicle({"type": "CAR"})
if not isinstance(v, Car):
    msg = f"Expected v to be an instance of Car, but got {type(v).__name__}"
    raise AssertionError(msg)

v = Vehicle({"num_doors": 4})
if not isinstance(v, Car):
    msg = f"Expected v to be an instance of Car, but got {type(v).__name__}"
    raise AssertionError(msg)

v = Vehicle({"type": "van"})
if not isinstance(v, Van):
    msg = f"Expected v to be an instance of Van but got {type(v).__name__}"
    raise AssertionError(msg)
