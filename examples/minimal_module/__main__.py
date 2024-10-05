# cmd: `python -m minimal_example` in th examples directory

from .vehicle import AutoVehicle, VehicleConfig  # noqa: TID252

config = VehicleConfig.from_dict({"type": "car"})

# Now you can create a car object using the configuration object with Auto*
car = AutoVehicle(config)

# Now you can access the config object
assert car.config.type == "car", f"expected 'car', got '{car.config.type}'"

print(type(car))
# <class 'minimal_module.vehicle.car.Car'>
