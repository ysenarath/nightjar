# Nightjar

[![PyPI version](https://badge.fury.io/py/nightjar.svg)](https://badge.fury.io/py/nightjar)
![PyPI - Downloads](https://img.shields.io/pypi/dm/nightjar)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/nightjar)
![GitHub](https://img.shields.io/github/license/ysenarath/nightjar)

## About Nightjar

Nightjar is a powerful Python package that brings the flexibility of configuration-based object creation to your projects. Inspired by the `huggingface/transformers` package, Nightjar allows you to effortlessly create and manage different types of objects based on simple configuration files.

## Installation

Get started with Nightjar in seconds:

```bash
pip install nightjar
```

## Quick Start

Here's a taste of how Nightjar can simplify your code:

```python
from nightjar import AutoModule, BaseConfig, BaseModule

class VehicleConfig(BaseConfig, dispatch=["type"]):
    type: str

class Vehicle(BaseModule):
    config: VehicleConfig

class Car(Vehicle):
    config: VehicleConfig

class Van(Vehicle):
    config: VanConfig

# Create a vehicle based on configuration
config = VehicleConfig.from_dict({"type": "car"})
vehicle = AutoModule(config)

print(type(vehicle))  # <class '__main__.Car'>
```

## Documentation

For more detailed information, check out our [full documentation](https://github.com/ysenarath/nightjar/wiki).

## Contributing

We welcome contributions! Check out our [Contribution Guide](CONTRIBUTING.md) to get started.

## Support

Need help? Have questions? Join our [Discord community](https://discord.gg/nightjar) or open an [issue](https://github.com/ysenarath/nightjar/issues).

## License

Nightjar is released under the [MIT License](LICENSE).
