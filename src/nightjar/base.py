from __future__ import annotations

import abc
from collections.abc import Mapping
from dataclasses import dataclass, fields, is_dataclass
from typing import Any, ClassVar, Dict, Generator, Type

from typing_extensions import Self, dataclass_transform

from nightjar.annotations import get_annotations
from nightjar.types import DispatchRegistry, from_dict, to_dict

__all__ = [
    "AttributeMap",
    "BaseConifg",
    "BaseModule",
]


@dataclass_transform()
class AttributeMapMeta(abc.ABCMeta):
    def __new__(
        cls,
        __name: str,
        __bases: tuple[type, ...],
        __namespace: dict[str, Any],
        /,
        **kwargs,
    ):
        dispatch = kwargs.pop("dispatch", None)
        obj = super().__new__(cls, __name, __bases, __namespace)
        obj = dataclass(**kwargs)(obj)
        if hasattr(obj, "_dispatch_registry"):
            obj._dispatch_registry.register(obj)
        elif dispatch is not None:
            obj._dispatch_registry = DispatchRegistry(dispatch)
        return obj


class AttributeMap(Mapping, metaclass=AttributeMapMeta):
    def __getitem__(self, __key: Any) -> Any:
        if hasattr(self, __key):
            return getattr(self, __key)
        raise KeyError(__key)

    def __setattr__(self, __name: str, __value: Any) -> None:
        field_types = {field.name: field.type for field in fields(self)}
        __type = field_types[__name]
        if is_dataclass(__type) and not isinstance(__value, __type):
            __value = __type(**__value)
        return super().__setattr__(__name, __value)

    def __iter__(self) -> Generator[str, None, None]:
        yield from to_dict(self)

    def __len__(self) -> int:
        return len(to_dict(self))

    def to_dict(self) -> dict[str, Any]:
        return to_dict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        return from_dict(cls, data)


class BaseConifg(AttributeMap): ...


class BaseModule:
    config: BaseConifg

    def __init__(self, config: BaseConifg) -> None:
        super().__init__()
        self.config = config
        self.__post_init__()

    def __post_init__(self) -> None:
        pass

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        # read annotation from class
        config_class = get_annotations(cls).get("config", BaseConifg)
        if config_class is BaseConifg:
            return
        AutoModule.dispatch[config_class] = cls


class AutoModule(BaseModule):
    dispatch: ClassVar[Dict[str, Type[BaseModule]]] = {}

    def __new__(cls, config: Any) -> BaseModule:
        return cls.dispatch[config.__class__](config)
