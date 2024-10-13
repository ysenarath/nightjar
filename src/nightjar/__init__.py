from nightjar.base import AutoModule, BaseConfig, BaseModule

__version__ = "0.0.5"

__all__ = [
    "AutoModule",
    "BaseConfig",
    "BaseModule",
    # fancy names for above classes in case you want to use them
    "Jar",
    "JarConfig",
]


class JarConfig(BaseConfig): ...


class Jar(BaseModule): ...


class AutoJar(AutoModule): ...
