# 🦅 Nightjar

[![PyPI version](https://badge.fury.io/py/nightjar.svg)](https://badge.fury.io/py/nightjar) 
![PyPI - Downloads](https://img.shields.io/pypi/dm/nightjar)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/nightjar)
![GitHub](https://img.shields.io/github/license/ysenarath/nightjar)

## 🌟 Simplify Your Python Object Creation

Nightjar is a powerful Python package that brings the flexibility of configuration-based object creation to your projects. Inspired by the `huggingface/transformers` package, Nightjar allows you to effortlessly create and manage different types of objects based on simple configuration files.

## 🚀 Features

- **Dynamic Object Creation**: Create objects on-the-fly based on configuration
- **Type-Safe**: Leverage Python's type hinting for safer code
- **Flexible**: Easily extend and customize for your specific needs
- **Automated**: Let Nightjar handle the object instantiation logic for you
- **Standardized**: Bring consistency to your configuration-driven code
- **Compatible**: Jar* objects provide syntactic sugar for easy integration with existing projects

## 🛠 Installation

Get started with Nightjar in seconds:

```bash
pip install nightjar
```

## 🏁 Quick Start

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

## 🔀 Understanding Dispatch

Dispatch is a key concept in Nightjar that enables dynamic object creation and handling based on configuration. Here's what you need to know:

1. **Purpose**: Dispatch automatically selects and creates the appropriate object type based on the provided configuration.

2. **How it works**: 
   - In your configuration class, specify a "dispatch" parameter. This determines which attribute(s) will decide the specific object type to create.
   - Example: `class VehicleConfig(BaseConfig, dispatch=["type"]):`

3. **Object Creation**: 
   - `AutoModule` uses the dispatch mechanism to create the right object based on the configuration.
   - It maintains a dispatch dictionary mapping configuration classes to module classes.

4. **Serialization and Deserialization**: 
   - Dispatch is also used when converting objects to and from dictionaries, ensuring consistent handling of your custom types.

5. **Flexibility**: 
   - This mechanism makes Nightjar highly adaptable. You can easily add new object types by creating new configuration and module classes, without changing the core logic.

Dispatch is what gives Nightjar its power, allowing for truly dynamic, configuration-driven object handling in your projects.

## 🧩 Jar* Objects: Syntactic Sugar for Seamless Integration

Nightjar introduces Jar* objects (like AutoJar, BaseJar) as syntactic sugar to enhance compatibility with existing projects. These objects are especially useful when BaseModule and other class objects are already defined in your project or when using frameworks like Pydantic.

For example:

```python
from nightjar import AutoJar, BaseJar

# Use BaseJar instead of BaseModule if you already have a BaseModule in your project
class Vehicle(BaseJar):
    config: VehicleConfig

# Use AutoJar instead of AutoModule for consistency
vehicle = AutoJar(config)
```

This flexibility allows Nightjar to integrate smoothly with your existing codebase without naming conflicts.

## 🌈 Use Cases

Nightjar shines in various scenarios:

- **Machine Learning Pipelines**: Dynamically select and configure models
- **Plugin Systems**: Easily manage and load different plugins
- **Game Development**: Create game objects based on configuration files
- **Web Frameworks**: Dynamically instantiate controllers or middleware
- **IoT Systems**: Configure and manage different types of devices

## 📘 Documentation

For more detailed information, check out our [full documentation](https://github.com/ysenarath/nightjar/wiki).

## 🤝 Contributing

We welcome contributions! Check out our [Contribution Guide](CONTRIBUTING.md) to get started.

## 💬 Support

Need help? Have questions? Join our [Discord community](https://discord.gg/nightjar) or open an [issue](https://github.com/ysenarath/nightjar/issues).

## 📄 License

Nightjar is released under the [MIT License](LICENSE).

---

Built with ❤️ by the Nightjar team. Happy coding! 🎉
