from typing import ClassVar

from .base import Vehicle, VehicleConfig  # noqa: TID252


class VanConfig(VehicleConfig):
    type: ClassVar[str] = "van"


class Van(Vehicle):
    config: VanConfig
