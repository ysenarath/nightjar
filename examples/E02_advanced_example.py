from nightjar import BaseConfig, BaseModule, Field


class VehicleConfig(BaseConfig): ...


class Vehicle(BaseModule):
    config: VehicleConfig


class CarConfig(VehicleConfig):
    __match__ = (Field("type").str.eq("car", case=False)) | (
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


# will result in a Vehicle instance since no match found
try:
    v = Vehicle(None)
    msg = "Expected ValueError for None config"
    raise AssertionError(msg)
except ValueError:
    pass

# will result in a Car instance
v = Vehicle({"type": "CAR"})
if not isinstance(v, Car):
    msg = "Expected v to be an instance of Car"
    raise AssertionError(msg)

# this will also result in a Car instance due to num_doors
v = Vehicle({"num_doors": 4})
if not isinstance(v, Car):
    msg = "Expected v to be an instance of Car"
    raise AssertionError(msg)

# will result in a Van instance
v = Vehicle({"type": "van"})
if not isinstance(v, Van):
    msg = f"Expected v to be an instance of Van but got {type(v).__name__}"
    raise AssertionError(msg)


# will result in a Vehicle instance since no match found
v = Vehicle({"type": "Bicycle"})
if not isinstance(v, Vehicle):
    msg = "Expected v to be an instance of Vehicle"
    raise AssertionError(msg)
