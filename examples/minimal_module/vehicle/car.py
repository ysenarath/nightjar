from typing import ClassVar

from .base import Vehicle, VehicleConfig  # noqa: TID252


class CarConfig(VehicleConfig):
    type: ClassVar[str] = "car"


class Car(Vehicle):
    config: CarConfig
