from __future__ import annotations

import abc
import contextlib
from collections import defaultdict
from collections.abc import Callable, Mapping
from dataclasses import dataclass, fields, is_dataclass
from typing import Any, Generator, Generic, Type, TypeVar

from typing_extensions import Self, dataclass_transform

from nightjar.registry import DispatchRegistry
from nightjar.serializers import from_dict, to_dict
from nightjar.utils import get_annotations

__all__ = ["AttributeMap", "BaseConfig", "BaseModule"]

K = TypeVar("K")
V = TypeVar("V")
T = TypeVar("T")
DType = TypeVar("DType", bound="dict[Type[BaseConfig], set[Type[BaseModule]]]")

dispatch_map: DType = defaultdict(set)


def get_model_class(
    config_class: Type[BaseConfig] | BaseConfig,
) -> Type[BaseModule]:
    if isinstance(config_class, BaseConfig):
        config_class = type(config_class)
    candidates = dispatch_map[config_class]
    if not candidates:
        msg = f"No registered module for config type {config_class.__name__}"
        raise ValueError(msg)
    if len(candidates) > 1:
        msg = f"Multiple registered modules found for config type {config_class.__name__}, specifically {', '.join(c.__name__ for c in candidates)}"
        raise ValueError(msg)
    return next(iter(candidates))


@dataclass_transform()
class AttributeMapMeta(abc.ABCMeta):
    _dispatch_registry: DispatchRegistry

    def __new__(
        mcls,
        name: str,
        bases: tuple[type, ...],
        namespace: dict[str, Any],
        /,
        **kwargs,
    ):
        dispatch = kwargs.pop("dispatch", None)
        klass = super().__new__(mcls, name, bases, namespace)
        klass = dataclass(**kwargs)(klass)
        has_config_base = False
        with contextlib.suppress(Exception):
            has_config_base = BaseConfig in bases
        if hasattr(klass, "_dispatch_registry"):
            klass._dispatch_registry.register(klass)
        elif has_config_base:
            klass._dispatch_registry = DispatchRegistry(dispatch)
        return klass


class AttributeMap(Mapping[K, V], Generic[K, V], metaclass=AttributeMapMeta):
    def __getitem__(self, __key: Any) -> Any:
        if hasattr(self, __key):
            return getattr(self, __key)
        raise KeyError(__key)

    def __setattr__(self, __name: str, __value: Any) -> None:
        field_types = {field.name: field.type for field in fields(self)}
        cls = field_types[__name]
        val = __value
        if is_dataclass(cls) and not isinstance(val, cls):
            val = cls(**__value)
        return super().__setattr__(__name, val)

    def __iter__(self) -> Generator[str, None, None]:
        yield from to_dict(self)

    def __len__(self) -> int:
        return len(to_dict(self))

    def to_dict(self) -> dict[str, Any]:
        return to_dict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        return from_dict(cls, data)


class BaseConfig(AttributeMap): ...


class BaseModule:
    config: BaseConfig

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        # read annotation from class
        config_class = get_annotations(cls).get("config", BaseConfig)
        if config_class is BaseConfig:
            return
        dispatch_map[config_class].add(cls)

    def __init__(self, config: BaseConfig | dict) -> None:
        super().__init__()
        self.config = config
        self.__post_init__()

    def __post_init__(self) -> None:
        pass

    @property
    def config(self) -> BaseConfig:
        return self._config

    @config.setter
    def config(self, value: BaseConfig | dict) -> None:
        if not isinstance(value, BaseConfig):
            cls = type(self)
            config_class = get_annotations(cls).get("config", None)
            if config_class is None:
                msg = f"Could not determine config class for {cls.__name__}"
                raise ValueError(msg)
            value = from_dict(config_class, value)
        self._config = value


class AutoModule:
    def __new__(cls, config: BaseConfig) -> BaseModule:
        if isinstance(config, BaseConfig):
            config_class = type(config)
        else:
            if not isinstance(config, Mapping):
                msg = f"Expected config to be a Mapping or BaseConfig, got {type(config).__name__}"
                raise ValueError(msg)
            base_config_class = get_annotations(cls).get("config", None)
            if base_config_class is None:
                msg = f"Could not determine config class for {cls.__name__}"
                raise ValueError(msg)
            config = from_dict(base_config_class, config)
            config_class = type(config)
        if config_class in dispatch_map:
            klass = get_model_class(config_class)
            self = super().__new__(klass)
            self.__init__(config)
            return self
        msg = f"No module found for config type {type(config).__name__}"
        raise ValueError(msg) from None

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)


def register(*config: Type[BaseConfig]) -> Callable[[Type[T]], Type[T]]:
    def decorator(cls: Type[T]) -> Type[T]:
        for c in config:
            dispatch_map[c].add(cls)
        return cls

    return decorator


def dispatch(cls: Type[BaseConfig], config: dict) -> BaseModule:
    config = from_dict(cls, config)
    klass = get_model_class(config)
    return klass(config)
