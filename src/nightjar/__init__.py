from nightjar.base import AutoModule, BaseConifg, BaseModule

__version__ = "0.0.1"

__all__ = [
    "AutoModule",
    "BaseConifg",
    "BaseModule",
    # fancy names for above classes in case you want to use them
    "Jar",
    "JarConfig",
]


class JarConfig(BaseConifg): ...


class Jar(BaseModule): ...


class AutoJar(AutoModule): ...
