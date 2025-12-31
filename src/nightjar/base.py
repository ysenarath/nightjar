from __future__ import annotations

import abc
from collections.abc import Mapping
from dataclasses import dataclass, fields, is_dataclass
from typing import Any, ClassVar, Dict, Generator, Generic, Type, TypeVar

from typing_extensions import Self, dataclass_transform

from nightjar.annotations import get_annotations
from nightjar.registry import DispatchRegistry
from nightjar.types import from_dict, to_dict

__all__ = ["AttributeMap", "BaseConfig", "BaseModule"]

K = TypeVar("K")
V = TypeVar("V")


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
        obj = super().__new__(mcls, name, bases, namespace)
        obj = dataclass(**kwargs)(obj)
        if hasattr(obj, "_dispatch_registry"):
            obj._dispatch_registry.register(obj)
        elif dispatch is not None:
            obj._dispatch_registry = DispatchRegistry(dispatch)
        return obj


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


class BaseConfig(AttributeMap):
    pass


class BaseModule:
    config: BaseConfig

    def __init__(self, config: BaseConfig) -> None:
        super().__init__()
        self.config = config
        self.__post_init__()

    def __post_init__(self) -> None:
        pass

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        # read annotation from class
        config_class = get_annotations(cls).get("config", BaseConfig)
        if config_class is BaseConfig:
            return
        AutoModule.dispatch[config_class] = cls


class AutoModule(BaseModule):
    dispatch: ClassVar[Dict[str, Type[BaseModule]]] = {}

    def __new__(cls, config: Any) -> BaseModule:
        return cls.dispatch[config.__class__](config)
